"""
Módulo para la creación del orquestador.
"""

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from .system_prompts.orchestrator_sp import SYSTEM_PROMPT

from src.agents.system_prompts import orchestrator_sp

def create_pentest_orchestrator(model: ChatOpenAI):
    """
    Configura y devuelve el motor del orquestador.
    """
    
    # Lista de Herramientas(Agentes Especializados)
    tools = []

    # Construcción del Prompt
    prompt = SYSTEM_PROMPT

    # Construir el Agente
    agent = create_agent(model=model, tools=tools, system_prompt=prompt)

    return agent