from google.adk.agents import LlmAgent
from src.config import gemini_settings
from src.tools.normal_tools import construire_prompt_systeme_agent_normal


INSTRUCTION = (
    construire_prompt_systeme_agent_normal(
        sujet="Général",
        niveau="débutant",
        objectifs=["Expliquer clairement", "Donner des exemples simples"],
    )
)

agent_normal = LlmAgent(
    name="NormalAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,  
    description="Agent généraliste pour discuter et expliquer des notions sans générer d'exercices ni de cours.",
    instruction=INSTRUCTION,
    tools=[],
)

