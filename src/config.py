from pydantic_settings import BaseSettings, SettingsConfigDict
from google import genai

class AppSettings(BaseSettings):
    """Configuration de l'application."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    APP_NAME: str
    ENV: str
    HOST: str
    PORT: int
    DEBUG: bool


class GeminiSettings(BaseSettings):
    """Configuration pour Google Generative AI."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

    GOOGLE_API_KEY: str
    GEMINI_MODEL_2_5_FLASH: str
    GEMINI_MODEL_2_5_FLASH_LITE: str
    GEMINI_MODEL_2_5_FLASH_LIVE: str


    def __init__(self, **data):
        super().__init__(**data)
        
        self.CLIENT = genai.Client(api_key=self.GOOGLE_API_KEY)

# Instances des settings
app_settings = AppSettings()
gemini_settings = GeminiSettings() 
