from pydantic_settings import BaseSettings, SettingsConfigDict
from google import genai
import logging
from urllib.parse import quote_plus
import base64

logger = logging.getLogger(__name__)


class AppSettings(BaseSettings):
    """Configuration de l'application."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    APP_NAME: str
    ENV: str
    HOST: str
    PORT: int
    DEBUG: bool


class GeminiSettings(BaseSettings):
    """Configuration pour Google Generative AI."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="allow"
    )

    GOOGLE_API_KEY: str
    GEMINI_MODEL_2_5_FLASH: str
    GEMINI_MODEL_2_5_FLASH_LITE: str
    GEMINI_MODEL_2_5_FLASH_LIVE: str
    GEMINI_MODEL_2_5_FLASH_IMAGE: str

    def __init__(self, **data):
        super().__init__(**data)

        self.CLIENT = genai.Client(api_key=self.GOOGLE_API_KEY)


class DatabaseSettings(BaseSettings):
    """Configuration de la base de données PostgreSQL / Cloud SQL."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    DB_USER_SQL: str
    DB_PASSWORD_SQL: str
    DB_NAME_SQL: str
    DB_HOST_SQL: str
    DB_PORT_SQL: int = 5432

    @property
    def dsn(self) -> str:
        """Construit le DSN PostgreSQL complet (format asyncpg)."""
        encoded_password = quote_plus(self.DB_PASSWORD_SQL)
        dsn = f"postgresql://{self.DB_USER_SQL}:{encoded_password}@{self.DB_HOST_SQL}:{self.DB_PORT_SQL}/{self.DB_NAME_SQL}"
        logger.info(
            f"Database DSN generated for host {self.DB_HOST_SQL}:{self.DB_PORT_SQL}"
        )
        return dsn


class OAuthSettings(BaseSettings):
    """Configuration OAuth pour l'authentification."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    OIDC_GOOGLE_CLIENT_ID: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GOOGLE_CLIENT_SECRET_B64: str


    @property
    def GOOGLE_CLIENT_SECRET(self) -> str:
        """Retourne le client_secret décodé depuis Base64."""
        return base64.b64decode(self.GOOGLE_CLIENT_SECRET_B64).decode()
    
# Instances des settings
app_settings = AppSettings()  # type: ignore
gemini_settings = GeminiSettings()
database_settings = DatabaseSettings()
oauth_settings = OAuthSettings()
