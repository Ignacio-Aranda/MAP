from .factory import create_specialist
from .agent_config import VULN_PROMPT, VULN_TOOLS

def get_vulner_node(model):
    base = create_specialist(
        model=model,
        system_prompt=VULN_PROMPT,
        tools=VULN_TOOLS,
        state_keys=["vulnerabilidades", "hallazgos"], # Que estados puede actualizar
        shared_state_keys=["servicios", "hallazgos"]  # De donde puede leer
    )

    # Envolvemos el agente para saber cuantas veces se ha ejecutado y si pidió ejecutar una herramienta o 
    # bien hace falta que se vuelva a llamar por algún motivo (requeue)
    def wrapped(state): 
        out = base(state)
        out["vuln_attempts"] = int(state.get("vuln_attempts", 0) or 0) + 1
        msgs = out.get("messages", [])
        if msgs and hasattr(msgs[0], "tool_calls") and msgs[0].tool_calls:
            out["next_node_after_tool"] = "VULNER"
        if out.get("requeue"):
            out["next_node_after_tool"] = "VULNER"
        return out

    return wrapped 