from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import httpx
import os

from agents.orchestrator import get_orchestrator
from agents.agents import create_specialist
from state import PentestState

import agents.agent_config as agent_config

load_dotenv()

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

scanner_node = create_specialist(model=model, system_prompt=agent_config.SCAN_PROMPT, tools=agent_config.SCAN_TOOLS)
exploit_node = create_specialist(model=model, system_prompt=agent_config.EXPLOIT_PROMPT, tools=agent_config.EXPLOIT_TOOLS)

# Construcción del Grafo
builder = StateGraph(PentestState)

builder.add_node("ORCHESTRATOR", orchestrator_node)
builder.add_node("SCANNER", scanner_node)
builder.add_node("EXPLOITER", exploit_node)

# Flujo estrella: Agentes -> Orquestador
builder.add_edge("SCANNER", "ORCHESTRATOR")
builder.add_edge("EXPLOITER", "ORCHESTRATOR")

# Orquestador -> Siguiente paso (Condicional)
builder.add_conditional_edges(
    "ORCHESTRATOR",
    lambda state: state["next_node"],
    {
        "SCANNER": "SCANNER",
        "EXPLOITER": "EXPLOITER",
        "FINISH": END
    }
)

builder.set_entry_point("ORCHESTRATOR")
graph = builder.compile()

# Ejecución
if __name__ == "__main__":
    inputs = {
        "objetivos": ["172.22.0.20"],
        "messages": [("user", "Empieza el reconocimiento de 172.22.0.20.")],
        "hallazgos": []
    }
    # for output in graph.stream(inputs):
    #     print(output)
    for event in graph.stream(inputs):
        for node_name, state_update in event.items():
            for key, value in state_update.items():
                print(f"El nodo {node_name} actualiza el estado '{key}' con el valor: {value}")
