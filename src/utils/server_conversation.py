import os, asyncio, json
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from google.genai.types import (
    ActivityHandling,
    AudioTranscriptionConfig,
    AutomaticActivityDetection,
    Blob,
    Content,
    EndSensitivity,
    FunctionResponse,
    LiveConnectConfig,
    Part,
    PrebuiltVoiceConfig,
    RealtimeInputConfig,
    SpeechConfig,
    StartSensitivity,
    TurnCoverage,
    VoiceConfig,
)

from src.config import gemini_settings
from src.prompts.conversational_prompt import AGENT_PROMPT_ConversationAgent
from src.prompts.conversational_prompt import AGENT_PROMPT_ConversationAgentSpeechPresentation

GOOGLE_API_KEY = gemini_settings.GOOGLE_API_KEY
MODEL_LIVE = gemini_settings.GEMINI_MODEL_REALTIME

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

genai_client = genai.Client(api_key=GOOGLE_API_KEY)

class StartLiveBody(BaseModel):
    topic: str
    language: str = "fr-FR"
    context_summary: Optional[str] = None
    response_voice: Optional[str] = None  

@app.post("/live/start")
async def start_live(body: StartLiveBody):
    """
    Tool-call target: crée un 'ticket' de session côté serveur.
    Le front n'a besoin que de l'URL WS + session_id.
    """
    session_id = os.urandom(9).hex()

    ws_url = f"/ws/live/{session_id}"
    return {"session_id": session_id, "ws_url": ws_url}

@app.websocket("/ws/live/{session_id}")
async def ws_live(websocket: WebSocket, session_id: str):
    """
    Bridge bidirectionnel:
      - Client -> (binary PCM16 16k mono) -> Gemini Live
      - Gemini Live (audio 24kHz + events) -> Client
    Protocole minimal:
      - binaire = chunks audio PCM16
      - texte JSON = commandes, ex: {"type":"text","data":"..."} ou {"type":"close"}
    """
    await websocket.accept()
    interruptible = True # Permet d'interrompre la génération en parlant 

    config = LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription=AudioTranscriptionConfig(),
            input_audio_transcription=AudioTranscriptionConfig(),
            speech_config=SpeechConfig(
                voice_config=VoiceConfig(
                    prebuilt_voice_config=PrebuiltVoiceConfig(
                        voice_name="Puck"
                    )
                )
            ),
            language_code="fr-FR",
            # tools=self.tools.values(),
            system_instruction=Content(
                parts=[Part(text=AGENT_PROMPT_ConversationAgent)]
            ),
            realtime_input_config=RealtimeInputConfig(
                automatic_activity_detection=AutomaticActivityDetection(
                    disabled=False,
                    start_of_speech_sensitivity=StartSensitivity.START_SENSITIVITY_LOW,
                    end_of_speech_sensitivity=EndSensitivity.END_SENSITIVITY_LOW,
                    prefix_padding_ms=50,
                    silence_duration_ms=400,
                )
            ),
            activity_handling=(
                ActivityHandling.START_OF_ACTIVITY_INTERRUPTS
                if interruptible
                else ActivityHandling.NO_INTERRUPTION
            ),
            turn_coverage=TurnCoverage.TURN_INCLUDES_ONLY_ACTIVITY,
        )

    # Ouvre la session Live Gemini (SDK officiel)
    try:
        async with genai_client.aio.live.connect(model=MODEL_LIVE, config=config) as session:

            async def client_to_gemini():
                try:
                    while True:
                        msg = await websocket.receive()
                        if "bytes" in msg and msg["bytes"] is not None:
                            # Audio binaire en PCM16 16k mono
                            await session.send_realtime_input(
                                audio=types.Blob(
                                    data=msg["bytes"],
                                    mime_type="audio/pcm;rate=16000"
                                )
                            )
                        elif "text" in msg and msg["text"] is not None:
                            try:
                                obj = json.loads(msg["text"])
                            except Exception:
                                continue
                            t = obj.get("type")
                            if t == "text":
                                await session.send_realtime_input(text=obj.get("data",""))
                            elif t == "close":
                                await session.close()
                                await websocket.close()
                                break
                except WebSocketDisconnect:
                    pass

            async def gemini_to_client():
                async for message in session.receive():
                    if getattr(message, "data", None):
                        await websocket.send_bytes(message.data)
                    if getattr(message, "server_content", None):
                        sc = message.server_content
                        if getattr(sc, "turn_complete", False):
                            await websocket.send_text(json.dumps({"event":"turn_complete"}))

            await asyncio.gather(client_to_gemini(), gemini_to_client())

    except Exception as e:
        await websocket.send_text(json.dumps({"error": str(e)}))
        await websocket.close()
