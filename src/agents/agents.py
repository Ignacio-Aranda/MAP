from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

def create_specialist(model: ChatOpenAI, system_prompt: str, tools: list):
    # Aquí sí usamos create_react_agent para los agentes que usen herramientas
    return create_react_agent(model, tools, prompt=system_prompt)