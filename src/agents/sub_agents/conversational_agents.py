from google.adk.agents import LlmAgent
from src.config import gemini_settings
from src.prompts import AGENT_PROMPT_ConversationAgent, AGENT_PROMPT_ConversationPrecisionAgent
from src.tools import start_live_session


# speech_conversation_agent = LlmAgent(
#     name="SpeechConversationAgent",
#     model=gemini_settings.GEMINI_MODEL_2_5_REALTIME, 
#     description="Agent spécialisé dans la génération de conversations orales.",
#     instruction=AGENT_PROMPT_ConversationAgent,
#     tools=[],
# )
textual_conversation_agent = LlmAgent(
    name="TextualConversationAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH,
    description="Agent spécialisé dans la génération de conversations textuelles.",
    instruction=AGENT_PROMPT_ConversationAgent,
    tools=[],
)
conversation_precision_agent = LlmAgent(
    name="ConversationPrecisionAgent",
    model=gemini_settings.GEMINI_MODEL_2_5_FLASH_LITE,
    description="Agent permetant de définir la conversation qui aura lieu.",
    instruction=AGENT_PROMPT_ConversationPrecisionAgent,
    sub_agents=[textual_conversation_agent],
    tools=[start_live_session],
    output_key="precision_response",
    # output_key="precision_response.role_agent,precision_response.topic,precision_response.type",
)

# precision_reponse=
# {
#     role: "assistant",
#     topic: "interviewer",
#     type: "speech",
# }