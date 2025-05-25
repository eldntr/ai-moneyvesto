# app/config.py
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

class Config:
    """Menampung semua variabel konfigurasi aplikasi."""
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
    YOUR_SITE_URL = os.getenv("YOUR_SITE_URL", "http://localhost:5000")
    YOUR_APP_NAME = os.getenv("YOUR_APP_NAME", "My Modular Chatbot")