""" Este módulo incluye el flujo principal del sistema """

import os
import httpx
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.agents.orchestrator_agent import create_pentest_orchestrator

async def main() -> None:
    """
    Punto de entrada para la ejecución del orquestador de pentest.
    """

    model = ChatOpenAI(
        model="gemma4:26b", 
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        http_client=httpx.Client(verify=False),
        temperature=0, 
    )

    # Definimos el objetivo del pentest
    user_prompt = "Hola, que tal, todo preparado?"

    # Inicializamos el orquestador
    pentest_orchestrator = create_pentest_orchestrator(model)

    print("--- [Iniciando Pentest] ---")

    try:
        # 3. Lanzamos el agente de forma asíncrona
        result = pentest_orchestrator.invoke(
            {"messages": [{"role": "user", "content": user_prompt}]}
        )

        print(result["messages"][-1].content)

    except Exception as e:
        print(f"[!] Error durante la ejecución: {e}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())