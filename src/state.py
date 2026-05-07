from typing import Dict, TypedDict, Annotated, List, Any
from langchain_core.messages import BaseMessage
import operator

class PentestState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add] # Historial de mensajes entre agentes, orquestador y herramientas. Se van acumulando a lo largo del proceso.
    objetivos: List[str] # Lista de todos los objetivos que se han identificado para el pentest
    servicios: Dict[str, Any]
    hallazgos: Annotated[List[str], operator.add] # Lo que vayan descubriendo los agentes y sea relevante para un pentest
    vulnerabilidades: Dict[str, Any] # Diccionario con vulnerabilidades, incluiye el estado (por_explotar, explotada, falsa_alarma)
    next_node: str  # El orquestador escribe aquí qué nodo es el siguiente.