import os
from typing import ClassVar, List, Optional

from dotenv import load_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # Pydantic v2 configuration
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )
    
    # API Settings
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = Field(default="Vibe Mapping Agent API")
    
    # Server Settings
    PORT: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")
    DEBUG: bool = Field(default=True)
    RELOAD: bool = Field(default=True)
    
    # CORS Settings - now a regular field, not a property
    CORS_ORIGINS_STR: str = Field(default="http://localhost:3000")
    cors_allow_origins: List[str] = Field(default_factory=list)
    
    # Database Settings
    SUPABASE_URL: Optional[str] = Field(default=None)
    SUPABASE_KEY: Optional[str] = Field(default=None)
    DATABASE_URL: Optional[str] = Field(default=None)
    
    # LLM API Settings
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    PORTKEY_API_KEY: Optional[str] = Field(default=None)
    PORTKEY_VIRTUAL_KEY: Optional[str] = Field(default=None)
    PORTKEY_GATEWAY_URL: Optional[str] = Field(default="https://api.portkey.ai/v1/proxy")
    LLM_MODEL: Optional[str] = Field(default="gemini-2.0-flash")
    
    # Environment detection
    IS_STREAMLIT: bool = Field(default=False)
    
    @model_validator(mode="after")
    def parse_cors_origins(self):
        origins = self.CORS_ORIGINS_STR
        if origins:
            self.cors_allow_origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
        if not self.cors_allow_origins:
            self.cors_allow_origins = ["http://localhost:3000"]
        return self
    
    @model_validator(mode="after")
    def parse_boolean_env_vars(self):
        # Parse boolean environment variables from strings
        debug_str = os.getenv("DEBUG", "True")
        reload_str = os.getenv("RELOAD", "True")
        is_streamlit_str = os.getenv("IS_STREAMLIT", "False")
        
        self.DEBUG = debug_str.lower() in ("true", "1", "t")
        self.RELOAD = reload_str.lower() in ("true", "1", "t")
        self.IS_STREAMLIT = is_streamlit_str.lower() in ("true", "1", "t")
        return self

# Create a global settings object that can be imported and used throughout the app
settings = Settings()
