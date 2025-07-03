# app/config.py
import os
from typing import List
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # API Configuration
    app_name: str = Field("Healthcare Database Assistant API", env="APP_NAME")
    app_version: str = Field("1.0.0", env="APP_VERSION")
    debug: bool = Field(False, env="DEBUG")
    
    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    reload: bool = Field(False, env="RELOAD")
    
    # CORS Configuration
    cors_origins: List[str] = Field(["*"], env="CORS_ORIGINS")
    cors_methods: List[str] = Field(["*"], env="CORS_METHODS")
    cors_headers: List[str] = Field(["*"], env="CORS_HEADERS")
    
    # Database Configuration
    db_host: str = Field(..., env="DB_HOST")
    db_port: int = Field(5432, env="DB_PORT")
    db_name: str = Field(..., env="DB_NAME")
    db_user: str = Field(..., env="DB_USER")
    db_password: str = Field(..., env="DB_PASSWORD")
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(..., env="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field("2024-02-15-preview", env="AZURE_OPENAI_API_VERSION")
    azure_openai_deployment_name: str = Field(..., env="AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_model_name: str = Field("gpt-4", env="AZURE_OPENAI_MODEL_NAME")
    
    # Agent Configuration
    max_query_length: int = Field(1000, env="MAX_QUERY_LENGTH")
    max_chat_message_length: int = Field(2000, env="MAX_CHAT_MESSAGE_LENGTH")
    max_results_limit: int = Field(1000, env="MAX_RESULTS_LIMIT")
    query_timeout_seconds: int = Field(120, env="QUERY_TIMEOUT_SECONDS")
    
    # Session Configuration
    session_timeout_hours: int = Field(24, env="SESSION_TIMEOUT_HOURS")
    max_session_history: int = Field(100, env="MAX_SESSION_HISTORY")
    
    # Storage Configuration
    session_storage_path: str = Field("sessions", env="SESSION_STORAGE_PATH")
    json_responses_path: str = Field("json_responses", env="JSON_RESPONSES_PATH")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    
    # Security Configuration
    api_key: str = Field(None, env="API_KEY")
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()

# Validation functions
def validate_settings():
    """Validate required settings"""
    required_fields = [
        "db_host", "db_name", "db_user", "db_password",
        "azure_openai_endpoint", "azure_openai_api_key", "azure_openai_deployment_name"
    ]
    
    missing_fields = []
    for field in required_fields:
        if not getattr(settings, field):
            missing_fields.append(field.upper())
    
    if missing_fields:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")

# Database URL
def get_database_url() -> str:
    """Get database URL for SQLAlchemy"""
    return (f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}"
            f"@{settings.db_host}:{settings.db_port}/{settings.db_name}")

# Azure OpenAI configuration
def get_azure_openai_config() -> dict:
    """Get Azure OpenAI configuration"""
    return {
        "azure_endpoint": settings.azure_openai_endpoint,
        "api_key": settings.azure_openai_api_key,
        "api_version": settings.azure_openai_api_version,
        "deployment_name": settings.azure_openai_deployment_name,
        "model": settings.azure_openai_model_name
    }