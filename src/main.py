from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
import httpx
import json
import os
from copy import deepcopy

from agents.orchestrator import get_orchestrator
from agents.scanner import get_scanner_node
from agents.vulner import get_vulner_node
from state import PentestState

import agents.agent_config as agent_config

load_dotenv()


def _format_message(message):
    if hasattr(message, "type") and hasattr(message, "content"):
        content = str(message.content).replace("\n", " ").strip()
        if len(content) > 220:
            content = content[:217] + "..."
        return f"{message.type}: {content}"
    if isinstance(message, tuple):
        content = str(message[1]).replace("\n", " ").strip()
        if len(content) > 220:
            content = content[:217] + "..."
        return f"{message[0]}: {content}"
    return str(message)


def _count_nested_items(mapping):
    return sum(len(items) for items in (mapping or {}).values())


def _summarize_event(event, previous_event, step_number):
    changed_keys = []
    if previous_event:
        for key, value in event.items():
            if previous_event.get(key) != value:
                changed_keys.append(key)
    else:
        changed_keys = sorted(event.keys())

    messages = event.get("messages", [])
    return {
        "step": step_number,
        "next_node": event.get("next_node"),
        "scan_attempts": event.get("scan_attempts", 0),
        "vuln_attempts": event.get("vuln_attempts", 0),
        "servicios_detectados": _count_nested_items(event.get("servicios")),
        "vulnerabilidades_detectadas": _count_nested_items(event.get("vulnerabilidades")),
        "hallazgos_totales": len(event.get("hallazgos", []) or []),
        "ultimo_mensaje": _format_message(messages[-1]) if messages else None,
        "campos_modificados": changed_keys,
    }

def router_after_agent(state: PentestState):
    # Miramos el último mensaje que ha enviado el agente
    last_message = state["messages"][-1]
    
    # Si el mensaje contiene peticiones de herramientas:
    if last_message.tool_calls:
        return "TOOLS" # Lo mandamos al nodo de herramientas para que las ejecute
    
    # Si no hay peticiones, es que el agente ha respondido con texto:
    return "ORCHESTRATOR"

def router_after_tools(state: PentestState):
    for message in reversed(state.get("messages", [])):
        tool_calls = getattr(message, "tool_calls", None)
        if not tool_calls:
            continue

        tool_name = None
        first_call = tool_calls[0]
        if isinstance(first_call, dict):
            tool_name = first_call.get("name")
        else:
            tool_name = getattr(first_call, "name", None)

        if tool_name == "nmap_scan":
            return "SCANNER"
        if tool_name == "search_exploits":
            return "VULNER"
        break

    return state.get("next_node_after_tool", "ORCHESTRATOR")

# Configuracion del modelo
model = ChatOpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
    http_client=httpx.Client(verify=False, timeout=60.0),
    model=os.getenv("OPENAI_MODEL"),
    temperature=0
) 

# Creamos los Agentes
orchestrator_node = get_orchestrator(model)

scanner_node = get_scanner_node(model)
vulner_node = get_vulner_node(model)

# Construcción del Grafo
builder = StateGraph(PentestState)

builder.add_node("ORCHESTRATOR", orchestrator_node)
builder.add_node("SCANNER", scanner_node)
builder.add_node("VULNER", vulner_node)

tools_node = ToolNode(agent_config.SCAN_TOOLS + agent_config.VULN_TOOLS)
builder.add_node("TOOLS", tools_node)

# Flujo Agentes -> Orquestador

# Cuando vengas de SCANNER si la el último mensaje tiene tool_calls, ve a TOOLS, sino a ORCHESTRATOR
builder.add_conditional_edges(
    "SCANNER",
    router_after_agent,
    {
        "TOOLS": "TOOLS",
        "ORCHESTRATOR": "ORCHESTRATOR"
    }
)

# Cuando vengas de VULNER si la el último mensaje tiene tool_calls, ve a TOOLS, sino a ORCHESTRADOR
builder.add_conditional_edges(
    "VULNER",
    router_after_agent,
    {
        "TOOLS": "TOOLS",
        "ORCHESTRATOR": "ORCHESTRATOR"
    }
)

# Cuando vengas de TOOLS mira la última herramienta llamada para decidir a dónde ir
# (si nmap_scan -> SCANNER, si search_exploits -> VULNER, sino ORCHESTRATOR)
builder.add_conditional_edges(
    "TOOLS",
    router_after_tools,
    {
        "SCANNER": "SCANNER",
        "VULNER": "VULNER",
        "ORCHESTRATOR": "ORCHESTRATOR",
        "FINISH": END
    }
)

# Orquestador -> Siguiente paso (Condicional)

# Cuando vengas del orquestador, mira el estado "next_node" para decidir a dónde ir (SCANNER -> SCANNER, VULNER -> VULNER, FINISH -> END)
builder.add_conditional_edges(
    "ORCHESTRATOR",
    lambda state: state["next_node"],
    {
        "SCANNER": "SCANNER",
        "VULNER": "VULNER",
        "FINISH": END
    }
)

# Punto de inicio
builder.set_entry_point("ORCHESTRATOR")
graph = builder.compile()

# Ejecución
if __name__ == "__main__":
    inputs = {
        "objetivos": ["172.22.0.20"],
        "messages": [("user", "Busca todas las vulnerabilidades del objetivo")],
        "hallazgos": [],
        "scan_attempts": 0,
        "vuln_attempts": 0,
    }

    print("--- Iniciando Pentest (Monitorea 'estado_actual.json' para ver cambios) ---")

    previous_event = None
    trace_path = "trace_actual.jsonl"
    with open(trace_path, "w", encoding="utf-8") as trace_file:
        for step_number, event in enumerate(graph.stream(inputs, stream_mode="values"), start=1):
            with open("estado_actual.json", "w", encoding="utf-8") as f:
                estado_legible = deepcopy(event)

                mensajes_procesados = []
                for m in event.get("messages", []):
                    mensajes_procesados.append(_format_message(m))

                estado_legible["messages"] = mensajes_procesados

                json.dump(estado_legible, f, indent=4, ensure_ascii=False)

            summary = _summarize_event(event, previous_event, step_number)
            trace_file.write(json.dumps(summary, ensure_ascii=False) + "\n")
            trace_file.flush()

            print(
                f"Paso {step_number} | siguiente={summary['next_node']} | "
                f"servicios={summary['servicios_detectados']} | vulns={summary['vulnerabilidades_detectadas']} | "
                f"scan={summary['scan_attempts']} | vuln={summary['vuln_attempts']}"
            )
            if summary["ultimo_mensaje"]:
                print(f"  ultimo={summary['ultimo_mensaje']}")

            previous_event = deepcopy(event)