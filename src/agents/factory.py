import json
import re
from langchain_core.messages import SystemMessage

def create_specialist(model, system_prompt: str, tools: list, state_keys: list = None, shared_state_keys: list = None):
    model_with_tools = model.bind_tools(tools)

    # Elimina los bloques de codigo markdown que pueda crear el LLM
    def _parse_structured_response(content: str, keys: list):
        clean_content = content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_content)
        parsed = {}
        # Si teniamos clave de next_node_after_tool o de requeue le dejamos devolverlo
        for ctrl in ("next_node_after_tool", "requeue"):
            if ctrl in data:
                parsed[ctrl] = data[ctrl]
        # Solo devolvemos las claves que nos interesan para el estado, ignorando el resto
        for key in keys:
            if key in data:
                parsed[key] = [data[key]] if key == "hallazgos" else data[key]
        return parsed

    # Extraemos la última salida de herramienta del historial, buscando mensajes de tipo "tool" desde el final.
    def _extract_last_tool_output(messages: list):
        for msg in reversed(messages):
            if getattr(msg, "type", None) == "tool":
                return str(getattr(msg, "content", ""))
        return ""

    # Fallback específico para SCANNER: Si el agente no devuelve JSON parseable pero sí hay salida de Nmap, intentamos extraer servicios y generar hallazgos básicos.
    def _fallback_from_nmap(tool_output: str, objetivos: list):
        if not tool_output or "PORT" not in tool_output:
            return None

        service_lines = []
        for line in tool_output.splitlines():
            if re.match(r"^\d+/(tcp|udp)\s+open\s+", line.strip()):
                service_lines.append(line.strip())

        if not service_lines:
            return None

        servicios = []
        for line in service_lines:
            # Formato típico: 22/tcp  open  ssh  OpenSSH 4.7...
            parts = re.split(r"\s+", line, maxsplit=3)
            if len(parts) < 3:
                continue
            port_proto = parts[0]
            nombre = parts[2]
            version = parts[3] if len(parts) > 3 else "unknown"
            puerto, protocolo = port_proto.split("/", 1)
            try:
                puerto_num = int(puerto)
            except ValueError:
                continue
            servicios.append({
                "puerto": puerto_num,
                "protocolo": protocolo,
                "nombre": nombre,
                "version": version,
            })

        if not servicios:
            return None

        target = objetivos[0] if objetivos else "unknown_target"
        return {
            "servicios": {target: servicios},
            "hallazgos": [{
                "descripcion": f"Nmap detectó {len(servicios)} servicios abiertos en {target}.",
                "metodo": "nmap_scan",
                "importancia": "Base para análisis de vulnerabilidades y priorización de superficie de ataque.",
            }],
        }
    
    def specialist_node(state):
        # Construimos el mensaje de sistema mezclando el Prompt original con el los estados a los que se tiene acceso
        contexto_extra = ""
        if shared_state_keys:
            contexto_extra = "\n\n--- INFORMACIÓN DEL SISTEMA ACTUAL ---\n"
            for key in shared_state_keys:
                valor = state.get(key, [])
                contexto_extra += f"{key.upper()}: {valor}\n"
        
        # Si el agente debe escribir en estados, le recordamos que use JSON
        instruccion_json = ""
        if state_keys:
            instruccion_json = f"\nIMPORTANTE: Tu respuesta final DEBE ser un JSON válido que encaje con las claves: {state_keys}."


        full_prompt = f"{system_prompt}\n{contexto_extra}{instruccion_json}"
        messages = [SystemMessage(content=full_prompt)] + state["messages"]

        # Tras recibir un ToolMessage, invocamos sin tools para forzar una respuesta final parseable.
        active_model = model_with_tools
        response = active_model.invoke(messages)
        
        if response.tool_calls:
            return {"messages": [response]}

        final_response = response
        update = {"messages": [final_response]}

        # Intenta parsear la respuesta si se requiere estructura
        if state_keys:
            parsed = None
            try:
                parsed = _parse_structured_response(final_response.content, state_keys)
            except Exception:
                parsed = None

            # Reintento único para corregir formato JSON si viene respuesta libre.
            if not parsed:
                correction = (
                    f"Tu respuesta anterior no fue JSON válido parseable. "
                    f"Responde AHORA SOLO con un JSON válido con las claves exactas: {state_keys}. "
                    "Sin markdown, sin comentarios, sin texto adicional."
                )
                retry_messages = messages + [final_response, SystemMessage(content=correction)]
                retry_response = model.invoke(retry_messages)
                final_response = retry_response
                update["messages"] = [final_response]
                try:
                    parsed = _parse_structured_response(final_response.content, state_keys)
                except Exception:
                    parsed = None

            if parsed:
                update.update(parsed)
            else:
                preview = str(final_response.content)[:300]
                print(f"Error parseando JSON del agente tras reintento. Contenido: {preview}")

                # Fallback determinista para SCANNER cuando ya hay salida de tool de Nmap.
                if "servicios" in state_keys:
                    tool_output = _extract_last_tool_output(state.get("messages", []))
                    fallback = _fallback_from_nmap(tool_output, state.get("objetivos", []))
                    if fallback:
                        update["servicios"] = fallback["servicios"]
                        # hallazgos en estado usa operator.add; pasamos una lista de objetos.
                        update["hallazgos"] = fallback["hallazgos"]
                        print("Fallback aplicado: estados 'servicios' y 'hallazgos' actualizados desde salida de Nmap.")
        
        return update
    
    return specialist_node