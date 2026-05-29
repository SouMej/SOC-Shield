"""
SOC Platform Configuration
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Elasticsearch
    ES_HOST: str = Field(default="localhost", description="Elasticsearch host")
    ES_PORT: int = Field(default=9200, description="Elasticsearch port")
    ES_SCHEME: str = Field(default="http", description="Elasticsearch scheme")
    ES_INDEX_EVENTS: str = Field(default="soc-events", description="Events index pattern")
    ES_INDEX_ALERTS: str = Field(default="soc-alerts", description="Alerts index")
    ES_INDEX_AI: str = Field(default="soc-ai-analysis", description="AI analysis index")
    ES_INDEX_KB: str = Field(default="soc-knowledge", description="Knowledge base index")

    # AI Engine - Groq
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    AI_MODEL: str = Field(default="llama-3.3-70b-versatile", description="Groq model name")
    AI_TEMPERATURE: float = Field(default=0.1, description="LLM temperature")
    AI_POLL_INTERVAL: int = Field(default=10, description="AI polling interval in seconds")
    AI_BATCH_SIZE: int = Field(default=50, description="Events per AI analysis batch")

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, description="WebSocket heartbeat seconds")

    # Authentication
    JWT_SECRET: str = Field(default="soc-platform-secret-key-change-in-production", description="JWT secret")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRY_MINUTES: int = Field(default=480, description="JWT token expiry")

    # Log Simulator
    SIMULATOR_ENABLED: bool = Field(default=True, description="Enable log simulator")
    SIMULATOR_INTERVAL: float = Field(default=2.0, description="Simulator event interval seconds")

    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    CORS_ORIGINS: str = Field(default="http://localhost:5173,http://localhost:3000", description="CORS origins")

    @property
    def es_url(self) -> str:
        return f"{self.ES_SCHEME}://{self.ES_HOST}:{self.ES_PORT}"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
