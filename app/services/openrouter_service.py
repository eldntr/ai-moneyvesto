import requests
import base64
from app.config import Config
from io import BytesIO

class OpenRouterService:
    def __init__(self):
        self.api_key = Config.OPENROUTER_API_KEY
        self.api_base = Config.OPENROUTER_API_BASE
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY tidak ditemukan. Pastikan ada di file .env")

    def _encode_image_to_base64(self, image_file, image_format) -> str:
        buffered = BytesIO()
        image_file.save(buffered, format=image_format.upper())
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def get_chat_response(self, user_message: str, model: str = None) -> str:
        model = model or Config.DEFAULT_CHAT_MODEL
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
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"Error saat menghubungi OpenRouter: {e}")
            raise ConnectionError("Gagal terhubung ke layanan OpenRouter.")
        except (KeyError, IndexError) as e:
            print(f"Struktur respons API tidak valid: {e}")
            raise ValueError("Respons dari API tidak sesuai format yang diharapkan.")

    def get_vision_response(self, text_prompt: str, image_file, image_format: str, model: str = None) -> str:
        model = model or Config.DEFAULT_VISION_MODEL
        base64_image = self._encode_image_to_base64(image_file, image_format)
        
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
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": text_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/{image_format.lower()};base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ]
                }
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"Error saat menghubungi OpenRouter VLM: {e}")
            raise ConnectionError("Gagal terhubung ke layanan Vision AI.")
        except (KeyError, IndexError) as e:
            print(f"Struktur respons API VLM tidak valid: {e}")
            raise ValueError("Respons dari Vision API tidak sesuai format yang diharapkan.")

openrouter_service = OpenRouterService()