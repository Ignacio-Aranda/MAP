from langchain_openai import ChatOpenAI

from state import NodeName, PentestState


def _has_entries(mapping) -> bool:
    return any(bool(items) for items in (mapping or {}).values())

def get_orchestrator(model: ChatOpenAI):
    def orchestrator(state: PentestState):
        servicios = state.get("servicios", {}) or {}
        vulnerabilidades = state.get("vulnerabilidades", {}) or {}
        scan_attempts = int(state.get("scan_attempts", 0) or 0)
        vuln_attempts = int(state.get("vuln_attempts", 0) or 0)

        if not _has_entries(servicios):
            next_node = NodeName.SCANNER #  if scan_attempts < 1 else NodeName.FINISH
        elif not _has_entries(vulnerabilidades):
            next_node = NodeName.VULNER # if vuln_attempts < 1 else NodeName.FINISH
        else:
            next_node = NodeName.FINISH

        return {"next_node": next_node.value}
    return orchestrator