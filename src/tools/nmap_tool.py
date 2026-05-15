from langchain_core.tools import tool
from tools.run_command import run_command
import re


def _normalize_target(raw_target: str) -> str:
    """Extract a valid IPv4 from potentially noisy model output."""
    if isinstance(raw_target, (list, tuple, set)):
        for item in raw_target:
            normalized = _normalize_target(item)
            if normalized:
                return normalized

    if isinstance(raw_target, dict):
        for value in raw_target.values():
            normalized = _normalize_target(value)
            if normalized:
                return normalized

    candidate = (raw_target or "").strip()
    if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", candidate):
        return candidate

    match = re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", candidate)
    return match.group(0) if match else ""

@tool
def nmap_scan(arguments, target: str):
    """Realiza un escaneo de puertos básico usando Nmap en un objetivo. Se usa arguments para los argumentos de nmap
        Args:
            arguments (str): Argumentos para nmap (ej. -sV para detección de versiones)
            target (str): La IP a escanear (ej. 192.168.0.1)
    """
    target = _normalize_target(target)
    if not target:
        return "Error: target inválido. Debe ser una IPv4 válida, por ejemplo 172.22.0.20"
    print(f"Se ha ejecutado nmap: nmap {arguments} {target}")
    try:
        command = ["nmap", arguments, target]
        result = run_command(command)
        
        if not result or result.strip() == "":
            return "El comando Nmap se ejecutó pero no devolvió ningún resultado (salida vacía). Es el objetivo correcto? Esta accesible?"
        
        return result
        
    except Exception as e:
        return f"Error ejecutando nmap: {str(e)}"