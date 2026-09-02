import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "BankAssist AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"

    # LLM Settings (Groq)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "qwen/qwen3.6-27b"

    # MySQL Configuration
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "bankassist"
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root"
    
    # Custom Database URL (Optional SQLite or custom connection string)
    DATABASE_URL: Optional[str] = None

    # JWT Settings
    JWT_SECRET_KEY: str = "bankassist_super_secret_jwt_key_enterprise_rag_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # RAG & Embedding Settings
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_INDEX_NAME: str = "bankassist-banking-docs"
    PINECONE_ENVIRONMENT: str = "us-east-1"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    RETRIEVAL_THRESHOLD: float = 0.20
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K: int = 4

    # Uploads
    UPLOAD_DIRECTORY: str = "./data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 20

    class Config:
        env_file = ".env"
        extra = "allow"

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Default MySQL connection string
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

settings = Settings()

# Ensure required directories exist
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs("./data/sample_docs", exist_ok=True)
