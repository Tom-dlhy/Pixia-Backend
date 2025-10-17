from google.adk.agents import LlmAgent
from google.adk.tools import google_search  
from src.config import gemini_settings
from src.tools.normal_tools import construire_prompt_systeme_agent_normal

from src.tools.import_fichier_tools.recevoir_pdf import tool_spec_recevoir_et_lire_pdf




agent_normal = LlmAgent(
    name="NormalAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,  
    description="Agent généraliste pour discuter et expliquer des notions sans générer d'exercices ni de cours.",
    instruction=construire_prompt_systeme_agent_normal(
        sujet="Général", 
        niveau="débutant",
        objectifs=["Expliquer clairement", "Donner des exemples simples"]
    ),
     
)

_pdf_spec = tool_spec_recevoir_et_lire_pdf()
agent_normal.register_tool(
    name=_pdf_spec["name"],
    description=_pdf_spec["description"],
    input_schema=_pdf_spec["input_schema"],
    output_schema=_pdf_spec["output_schema"],
    handler=_pdf_spec["handler"],
)