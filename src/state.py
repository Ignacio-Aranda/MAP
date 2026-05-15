from typing import Dict, TypedDict, Annotated, List, Any, Optional
from pydantic import BaseModel
from enum import Enum
import operator

# Enums con los nombres de los nodos
class NodeName(str, Enum):
    ORCHESTRATOR = "ORCHESTRATOR"
    SCANNER = "SCANNER"
    VULNER = "VULNER"
    FINISH = "FINISH"

# Enums con los estados de las vulnerabilidades
class VulnStatus(str, Enum):
    POR_EXPLOTAR = "por_explotar"
    EXPLOTADA = "explotada"
    FALSA_ALARMA = "falsa_alarma"

# Estructuras de datos específicas
class Servicio(BaseModel):
    puerto: int
    protocolo: str
    nombre: str
    version: Optional[str] = "unknown"

class Hallazgo(BaseModel):
    descripcion: str
    metodo: str  # Cómo se consiguió
    importancia: str  # Por qué es importante

class Vulnerabilidad(BaseModel):
    nombre: str
    razon: str  # Por qué es vulnerable
    estado: VulnStatus = VulnStatus.POR_EXPLOTAR

class PentestState(TypedDict):
    messages: Annotated[List[Any], operator.add] # Historial de mensajes entre agentes, orquestador y herramientas. Se van acumulando a lo largo del proceso.
    objetivos: List[str] # Lista de todos los objetivos que se han identificado para el pentest. No será modificado
    servicios: Dict[str, List[Servicio]] # Podrá ser modificado por el Nodo Scanner
    hallazgos: Annotated[List[Hallazgo], operator.add] # Lo que vayan descubriendo los agentes y sea relevante para un pentest. Podrá ser modificado por cualquier Nodo.
    vulnerabilidades: Dict[str, List[Vulnerabilidad]] # Diccionario con vulnerabilidades, incluye el estado (por_explotar, explotada, falsa_alarma). Podrá ser modificado por el Nodo VulnFinder y Exploiter
    next_node: NodeName  # Indica el nodo es el siguiente. Podrá ser modificado por el Nodo Orquestador
    scan_attempts: int
    vuln_attempts: int