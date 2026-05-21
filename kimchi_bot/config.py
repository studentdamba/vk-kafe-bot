# Configuration and environment variables
from dotenv import load_dotenv
import os
from typing import List

load_dotenv()

class Settings:
    VK_TOKEN: str = os.getenv("VK_TOKEN", "")
    ADMIN_IDS: List[int] = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "database/kimchi_bot.db")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Session timeout in seconds (10 minutes)
    SESSION_TIMEOUT: int = 600
    
    # Cart cleanup interval in hours
    CART_CLEANUP_HOURS: int = 24

settings = Settings()
