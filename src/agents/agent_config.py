from tools.nmap_tool import nmap_scan
from tools.search_exploit_tool import search_exploits

# Prompts de Agentes Especialistas
SCAN_PROMPT = """
Eres un experto en escaneo de red. Analiza puertos y servicios en los objetivos dados. 
Tienes acceso a la herramienta nmap_scan para realizar escaneos. 
Informa de puertos abiertos y servicios detectados.
"""

EXPLOIT_PROMPT = """
Eres un experto en explotación. 
Tu meta es confirmar vulnerabilidades. 
No explotarlas, solo confirmalas con exploits conocidos.
"""

# Lista de Tools por agente
SCAN_TOOLS = [nmap_scan]
EXPLOIT_TOOLS = [search_exploits]