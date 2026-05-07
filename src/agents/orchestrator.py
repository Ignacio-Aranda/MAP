from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from state import PentestState

def get_orchestrator(model: ChatOpenAI):
    def orchestrator(state: PentestState):
        # El Orquestador decide basándose en el estado
        prompt = """Eres el jefe de un pentest. Basado en los hallazgos y objetivos, 
        decide quién es el siguiente: SCANNER, EXPLOITER o FINISH.
        Responde solo con el nombre en mayúsculas."""
        
        # Le pasamos todo el historial para que decida
        messages = [SystemMessage(content=prompt)] + state["messages"]
        response = model.invoke(messages)
        
        # Limpiamos la respuesta para quedarnos solo con el nodo
        decision = response.content.strip().upper()
        return {"next_node": decision}
    return orchestrator