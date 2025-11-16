"""
Configuration management for MindMentor
Loads settings from environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration"""
    
    # Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///mindmentor.db")
    DATABASE_PATH = Path(__file__).parent.parent.parent / "mindmentor.db"
    
    # Application Settings
    DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Session Configuration
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
    
    # LLM Settings
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
    ENABLE_LLM_CACHE = os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true"
    CACHE_TTL_DAYS = int(os.getenv("CACHE_TTL_DAYS", "7"))
    
    # Model selection for different tasks
    MODELS = {
        "pro": "gemini-2.5-pro",          # Complex tasks
        "flash": "gemini-2.5-flash",      # Standard tasks
        "flash_lite": "gemini-2.5-flash-lite"  # Simple tasks
    }
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please set it in .env file."
            )
        return True


# Singleton instance
config = Config()
