from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = ""
    
    # App Configuration
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    
    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # File Upload
    max_upload_size_mb: int = 10
    allowed_file_types: List[str] = [".pdf"]
    upload_dir: str = "uploads"
    
    # Vector Database
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "text-embedding-3-small"
    
    # Chat Configuration  
    chat_model: str = "gpt-4o-mini"  # Using gpt-4o-mini as gpt-4.1-mini doesn't exist
    max_tokens: int = 2000
    temperature: float = 0.7
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()