"""
WeatherWise Configuration Management
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    """Application settings."""
    
    # API Keys
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    def __init__(self):
        if not self.OPENWEATHER_API_KEY:
            raise ValueError("OPENWEATHER_API_KEY environment variable is required")

# Global settings instance
settings = Settings()