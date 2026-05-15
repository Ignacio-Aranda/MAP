from .factory import create_specialist
from .agent_config import SCAN_PROMPT, SCAN_TOOLS

def get_scanner_node(model):
    base = create_specialist(
        model=model,
        system_prompt=SCAN_PROMPT,
        tools=SCAN_TOOLS,
        state_keys=["servicios", "hallazgos"],
        shared_state_keys=["objetivos"]
    )

    # Envolvemos el agente para saber cuantas veces se ha ejecutado y si pidió ejecutar una herramienta o 
    # bien hace falta que se vuelva a llamar por algún motivo (requeue)
    def wrapped(state):
        out = base(state)
        out["scan_attempts"] = int(state.get("scan_attempts", 0) or 0) + 1
        msgs = out.get("messages", [])
        if msgs and hasattr(msgs[0], "tool_calls") and msgs[0].tool_calls:
            out["next_node_after_tool"] = "SCANNER"
        if out.get("requeue"):
            out["next_node_after_tool"] = "SCANNER"
        return out

    return wrapped