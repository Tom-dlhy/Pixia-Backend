# src/phone_ai/realtime_sessions/speech/sessions/gemini_realtime_session.py

import asyncio
import base64
import json
import queue
from typing import Callable, Optional, Dict, Any, List
from loguru import logger as Logger
import numpy as np
import genai
from google.auth.credentials import Credentials
from google.genai.live import AsyncSession
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

class GeminiRealtimeSession():
    """
    Handles a real-time streaming session with the Gemini model using audio input/output.
    """

    def __init__(
        self,
        system_instructions: str,
        voice_name: str = "Puck",
        model_name: str = "gemini-2.0-flash-live-001",
        language_code: str = "fr-FR",
        presentation_instructions: Optional[str] = None,
        on_close: Optional[Callable[[], None]] = None,
        credentials: Optional[Credentials] = None,
        prefix_padding_ms: int = 50,
        silence_duration_ms: int = 400,
        interruptible: bool = True,
        enable_conversation_logging: bool = False,
    ) -> None:
        """
        Initialize a Gemini real-time session.
        """
        self.voice_name = voice_name
        self.system_instructions = AGENT_PROMPT_ConversationAgent,
        self.presentation_instructions = AGENT_PROMPT_ConversationAgentSpeechPresentation,
        on_close=on_close,
        interruptible=interruptible,
        enable_conversation_logging=enable_conversation_logging,
        

        self.prefix_padding_ms = prefix_padding_ms
        self.silence_duration_ms = silence_duration_ms

        # self.google_cloud_project = google_cloud_project Pas necessaire ?
        # self.google_cloud_location = google_cloud_location
        # self.credentials = credentials

        self.language_code = language_code
        self.model_name = model_name

        # self.tools = TOOL APPEL COURS TA CAPTé 

        self.client = genai.Client(api_key=gemini_settings.GOOGLE_API_KEY)

        self.session: Optional[AsyncSession] = None

    async def run(self) -> None:
        """
        Launch the Gemini real-time session loop.

        Sets up connection config, starts the stream, handles incoming responses,
        and processes tool calls or audio responses.
        """
        Logger.info("Starting GeminiRealtimeSession...")
        self._loop = asyncio.get_running_loop()

        config = LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription=AudioTranscriptionConfig(),
            input_audio_transcription=AudioTranscriptionConfig(),
            speech_config=SpeechConfig(
                voice_config=VoiceConfig(
                    prebuilt_voice_config=PrebuiltVoiceConfig(
                        voice_name=self.voice_name
                    )
                )
            ),
            language_code=self.language_code,
            # tools=self.tools.values(),
            system_instruction=Content(
                parts=[Part(text=self.system_instructions)]
            ),
            realtime_input_config=RealtimeInputConfig(
                automatic_activity_detection=AutomaticActivityDetection(
                    disabled=False,
                    start_of_speech_sensitivity=StartSensitivity.START_SENSITIVITY_LOW,
                    end_of_speech_sensitivity=EndSensitivity.END_SENSITIVITY_LOW,
                    prefix_padding_ms=self.prefix_padding_ms,
                    silence_duration_ms=self.silence_duration_ms,
                )
            ),
            activity_handling=(
                ActivityHandling.START_OF_ACTIVITY_INTERRUPTS
                if self.interruptible
                else ActivityHandling.NO_INTERRUPTION
            ),
            turn_coverage=TurnCoverage.TURN_INCLUDES_ONLY_ACTIVITY,
        )

        try:
            async with self.client.aio.live.connect(
                model=self.model_name, config=config
            ) as session:
                self.session = session

                if self.presentation_instructions:
                    Logger.info(
                        f"Sending presentation instructions: {self.presentation_instructions}"
                    )
                    await session.send_client_content(
                        turns=Content(
                            role="user",
                            parts=[Part(text=self.presentation_instructions)],
                        )
                    )

                asyncio.create_task(self.audio_generator())

                while self.session is not None:
                    async for response in session.receive():
                        if hasattr(response, "server_content") and getattr(
                            response.server_content, "interrupted", False
                        ):
                            Logger.info(f"Interruption detected: {response}")
                            continue


                        # if getattr(response, "tool_call", None):
                        #     Logger.info(f"Tool call detected: {response.tool_call}")

                        #     function_responses: List[FunctionResponse] = []

                        #     for tool_call in response.tool_call.function_calls:
                        #         # If tool provided by ToolManager
                        #         if tool_call.name in self.tools:
                        #             tool_func = self.tools[tool_call.name]

                        #             # Allow a generic handler hook if you have one
                        #             tool_is_generic = False
                        #             tool_output: Any = None
                        #             try:
                        #                 # If you implement a generic handler on base class
                        #                 if hasattr(self, "_handle_generic_tool_calls"):
                        #                     tool_is_generic, tool_output = await self._handle_generic_tool_calls(
                        #                         tool_call.name, tool_call.args
                        #                     )
                        #                 if not tool_is_generic:
                        #                     tool_output = await tool_func(**tool_call.args) \
                        #                         if asyncio.iscoroutinefunction(tool_func) \
                        #                         else tool_func(**tool_call.args)
                        #             except Exception as te:
                        #                 tool_output = {"error": str(te)}

                        #             Logger.debug(
                        #                 f"Tool call {tool_call.name} returned: {tool_output}"
                        #             )

                        #             function_response = FunctionResponse(
                        #                 id=tool_call.id,
                        #                 name=tool_call.name,
                        #                 response={"result": tool_output},
                        #             )
                        #             function_responses.append(function_response)

                            # if function_responses:
                            #     Logger.info(
                            #         f"Sending tool responses: {function_responses}"
                            #     )
                            #     await self.session.send_tool_response(
                            #         function_responses=function_responses
                            #     )
                            # continue

                        # --- Raw audio bytes (assistant TTS audio)
                        if getattr(response, "data", None):
                            Logger.debug(
                                f"Audio data received: {len(response.data)} bytes"
                            )
                            audio_data = np.frombuffer(response.data, dtype=np.int16)
                            for sample in audio_data:
                                # Base class usually drains this queue to audio output device
                                self._audio_output_queue.put_nowait(sample)
                            continue

                Logger.debug("End response loop.")

        except SessionClosedException:
            Logger.info("Session closed via tool call.")
        except Exception as e:
            Logger.error(f"Error in GeminiRealtimeSession: {e}")
        finally:
            await self.close()

        Logger.info("GeminiRealtimeSession terminated.")

    
