"""
Configuration for AI Data Analyst.
Environment-driven, production-ready.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration from environment variables."""
    
    # LLM Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    LLM_BASE_URL: str = os.getenv(
        "LLM_BASE_URL",
        "https://openrouter.ai/api/v1"
    )
    LLM_TIMEOUT: float = float(os.getenv("LLM_TIMEOUT", "60.0"))
    
    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://analyst:analyst_password@postgres:5432/ecommerce"
    )
    
    # Application Configuration
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Safety Configuration
    QUERY_TIMEOUT_SECONDS: int = int(os.getenv("QUERY_TIMEOUT_SECONDS", "10"))
    MAX_QUERY_COST: int = int(os.getenv("MAX_QUERY_COST", "10000"))
    MAX_ROWS_PER_QUERY: int = int(os.getenv("MAX_ROWS_PER_QUERY", "1000"))
    DEFAULT_ROWS_PER_QUERY: int = int(os.getenv("DEFAULT_ROWS_PER_QUERY", "100"))
    MAX_QUERY_LENGTH: int = int(os.getenv("MAX_QUERY_LENGTH", "5000"))
    
    # Chart Configuration
    CHARTS_DIR: Path = Path(os.getenv("CHARTS_DIR", "charts"))
    
    # Agent Configuration
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "10"))
    
    @classmethod
    def get_api_key(cls) -> str:
        """Get LLM API key (OpenRouter or OpenAI)."""
        return cls.OPENROUTER_API_KEY or cls.OPENAI_API_KEY
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration. Returns list of errors."""
        errors = []
        
        if not cls.get_api_key():
            errors.append("OPENROUTER_API_KEY or OPENAI_API_KEY must be set")
        
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL must be set")
        
        return errors
    
    @classmethod
    def setup(cls):
        """Setup application (create directories, etc.)."""
        cls.CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def is_production(cls) -> bool:
        return cls.ENVIRONMENT.lower() == "production"


# Initialize on import
Config.setup()
