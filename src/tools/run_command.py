import subprocess

def run_command(command, timeout_sec=300):
    """Ejecuta un comando en la terminal del contenedor de pentest de forma no interactiva."""
    try:
        # Añadimos una validación por si le pasamos un string en lugar de lista
        if isinstance(command, str):
            command = command.split()
            
        full_command = ["docker", "exec", "pentest-sandbox"] + command
                
        result = subprocess.run(
            full_command, 
            capture_output=True, 
            text=True,
            timeout=timeout_sec
        )
        
        # Limpiamos los espacios en blanco
        stdout_str = result.stdout.strip()
        stderr_str = result.stderr.strip()
        
        print(f"--- Comando ejecutado: {' '.join(full_command)} ---")
        print(f"--- STDOUT ---\n{stdout_str}")
        print(f"--- STDERR ---\n{stderr_str}")
        
        # Si el comando falló a nivel de sistema operativo/Docker
        if result.returncode != 0:
            return (f"[!] El comando falló con código {result.returncode}.\n"
                    f"--- STDERR (Errores) ---\n{stderr_str}\n"
                    f"--- STDOUT ---\n{stdout_str}")
            
        # Si el comando funcionó pero no devolvió nada
        if not stdout_str and not stderr_str:
            return "[!] El comando se ejecutó correctamente pero devolvió una salida vacía."
            
        # Si funcionó pero escupió advertencias por stderr
        if stdout_str and stderr_str:
             return (f"--- STDOUT ---\n{stdout_str}\n\n"
                     f"--- ADVERTENCIAS (STDERR) ---\n{stderr_str}")
                     
        return stdout_str

    except subprocess.TimeoutExpired:
        return "[!] Error crítico: El comando excedió el tiempo máximo de ejecución de {} segundos.".format(timeout_sec)
    except Exception as e:
        return f"[!] Error interno de Python ejecutando Docker: {e}"