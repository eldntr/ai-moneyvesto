# app/services/openrouter_service.py
import requests
from app.config import Config

class OpenRouterService:
    """Service untuk berinteraksi dengan OpenRouter API."""

    def __init__(self):
        self.api_key = Config.OPENROUTER_API_KEY
        self.api_base = Config.OPENROUTER_API_BASE
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY tidak ditemukan. Pastikan ada di file .env")

    def get_chat_response(self, user_message: str, model: str = "google/gemini-flash-1.5") -> str:
        """
        Mengirim pesan ke OpenRouter dan mengembalikan respons dari model.
        """
        try:
            response = requests.post(
                url=f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": Config.YOUR_SITE_URL,
                    "X-Title": Config.YOUR_APP_NAME,
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": user_message}]
                }
            )
            response.raise_for_status()  # Error jika status code bukan 2xx
            data = response.json()
            return data['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"Error saat menghubungi OpenRouter: {e}")
            raise ConnectionError("Gagal terhubung ke layanan OpenRouter.")
        except (KeyError, IndexError) as e:
            print(f"Struktur respons API tidak valid: {e}")
            raise ValueError("Respons dari API tidak sesuai format yang diharapkan.")

# Membuat satu instance service untuk digunakan di seluruh aplikasi
openrouter_service = OpenRouterService()