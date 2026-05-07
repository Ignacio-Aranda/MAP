from langchain_core.tools import tool
from tools.run_command import run_command

@tool
def nmap_scan(arguments, target: str):
    """Realiza un escaneo de puertos básico usando Nmap en un objetivo. Se usa arguments para los argumentos de nmap
        Args:
            arguments (str): Argumentos para nmap (ej. -sV para detección de versiones)
            target (str): La IP a escanear (ej. 192.168.0.1)
    """
    target = target.strip()
    print(f"--- Ejecutando nmap {arguments} {target} ---")
    try:
        command = ["nmap", arguments, target]
        result = run_command(command)
        
        if not result or result.strip() == "":
            return "El comando Nmap se ejecutó pero no devolvió ningún resultado (salida vacía). Es el objetivo correcto? Esta accesible?"
        
        return result
        
    except Exception as e:
        return f"Error ejecutando nmap: {str(e)}"