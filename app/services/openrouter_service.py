# app/services/openrouter_service.py

import requests
import base64
from app.config import Config
from io import BytesIO
import json

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

    def get_chat_response(self, user_message: str, previous_chats: list = None, model: str = None) -> str:
        model = model or Config.DEFAULT_CHAT_MODEL
        previous_chats = previous_chats or []  # Default to an empty list if not provided

        # Construct the messages payload
        messages = [{"role": "user", "content": chat} for chat in previous_chats]
        messages.append({"role": "user", "content": user_message})

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
                    "messages": messages
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

    def record_finance(self, user_message: str, model: str = None) -> list:
        """
        Menganalisis pesan pengguna untuk mengekstrak transaksi keuangan menggunakan LLM.
        """
        model = model or Config.DEFAULT_CHAT_MODEL
        system_prompt = """
Anda adalah asisten pencatatan keuangan yang cerdas. Tugas Anda adalah mengubah teks transaksi dalam bahasa Indonesia menjadi format JSON yang terstruktur. Teks input bisa berisi satu atau lebih item transaksi.

**Aturan:**
1.  Identifikasi setiap item dalam pesan.
2.  Untuk setiap item, ekstrak informasi berikut:
    * `description`: Nama atau deskripsi barang/jasa. Buat deskripsi yang jelas dan ringkas.
    * `transaction_type`: Tentukan apakah ini 'withdrawal' (pengeluaran) atau 'deposit' (pemasukan). Kata kunci untuk 'withdrawal' termasuk 'beli', 'bayar', 'keluar', 'ongkos'. Kata kunci untuk 'deposit' termasuk 'dapat', 'gaji', 'jual', 'terima', 'masuk'.
    * `amount`: Jumlah atau kuantitas barang. Jika tidak disebutkan, anggap saja 1.
    * `total_price`: Harga total untuk item tersebut. Abaikan pemisah ribuan seperti titik atau koma saat mengekstrak angka.
3.  Format output HARUS berupa string JSON Array valid yang berisi objek-objek transaksi. Contoh: `[{"description": "...", ...}]`
4.  Jika ada item yang tidak memiliki harga, jangan masukkan ke dalam output. Setiap item harus memiliki harga.
5.  Jika Anda tidak dapat menemukan transaksi yang valid dalam pesan, kembalikan array JSON kosong `[]`.
6.  Interpretasikan singkatan harga seperti 'rb' sebagai 'ribu' (misal: 15rb = 15000). Jika ada kuantitas, kalikan harga satuan dengan kuantitas untuk mendapatkan `total_price`.

**Contoh Input -> Output:**
1. "saya membeli 1 galon aqua dengan harga 22000" -> `[{"description":"Aqua galon","transaction_type":"withdrawal","amount":1,"total_price":22000}]`
2. "hari ini beli 2 porsi nasi goreng 15rb dan es teh manis 5000" -> `[{"description":"Nasi Goreng","transaction_type":"withdrawal","amount":2,"total_price":30000},{"description":"Es Teh Manis","transaction_type":"withdrawal","amount":1,"total_price":5000}]`
3. "Dapat gaji bulan ini 5.000.000" -> `[{"description":"Gaji bulan ini","transaction_type":"deposit","amount":1,"total_price":5000000}]`
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
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "response_format": {"type": "json_object"}
                }
            )
            response.raise_for_status()
            data = response.json()
            content_str = data['choices'][0]['message']['content']
            
            # Membersihkan jika model membungkus output dengan markdown
            if content_str.strip().startswith('```json'):
                content_str = content_str.strip()[7:-3].strip()

            parsed_json = json.loads(content_str)

            # Menangani kasus jika model mengembalikan dict seperti {"transactions": [...]}
            if isinstance(parsed_json, dict) and len(parsed_json) == 1:
                return list(parsed_json.values())[0]
            
            if isinstance(parsed_json, list):
                return parsed_json

            raise ValueError("Format JSON dari API tidak dalam bentuk array.")

        except requests.exceptions.RequestException as e:
            print(f"Error saat menghubungi OpenRouter: {e}")
            raise ConnectionError("Gagal terhubung ke layanan OpenRouter.")
        except json.JSONDecodeError:
            print(f"Gagal mendekode JSON dari respons: {content_str}")
            raise ValueError("Gagal mem-parsing respons JSON dari API.")
        except (KeyError, IndexError) as e:
            print(f"Struktur respons API tidak valid: {e}")
            raise ValueError("Respons dari API tidak sesuai format yang diharapkan.")

    def get_tone_responses(self, vision_analysis: str, transactions: list, tone_type: str = "all", model: str = None) -> dict:
        """
        Generate responses with different tones based on transaction analysis.
        
        Args:
            vision_analysis: The vision analysis text
            transactions: List of structured transactions
            tone_type: Type of tone to generate ("supportive_cheerleader", "angry_mom", "wise_mentor", or "all")
            model: Model to use for generation
        
        Returns:
            Dictionary with tone responses
        """
        model = model or Config.DEFAULT_CHAT_MODEL
        
        # Calculate total amount for context
        total_amount = sum(transaction.get('total_price', 0) for transaction in transactions)
        
        # Define tone prompts
        tone_prompts = {
            "supportive_cheerleader": f"""
Berdasarkan analisis transaksi berikut: {vision_analysis}
Dan data transaksi terstruktur dengan total Rp {total_amount:,}

Berikan respons sebagai penasehat keuangan yang cheerful dan mendukung. Gunakan gaya bahasa yang positif, singkat, dan memberikan apresiasi atas kebiasaan mencatat keuangan. Fokus pada pencapaian dan motivasi. Maksimal 2-3 kalimat pendek.
""",
            "angry_mom": f"""
Berdasarkan analisis transaksi berikut: {vision_analysis}
Dan data transaksi terstruktur dengan total Rp {total_amount:,}

Berikan respons sebagai ibu yang khawatir dan sedikit kesal tentang pengeluaran. Gunakan gaya bahasa yang menunjukkan kekhawatiran, menegur dengan lembut, dan memberikan saran praktis untuk lebih berhemat. Gunakan bahasa sehari-hari seperti ibu berbicara dengan anaknya. Maksimal 2-3 kalimat pendek.
""",
            "wise_mentor": f"""
Berdasarkan analisis transaksi berikut: {vision_analysis}
Dan data transaksi terstruktur dengan total Rp {total_amount:,}

Berikan respons sebagai mentor bijaksana yang memberikan analisis singkat tentang pola pengeluaran. Fokus pada edukasi finansial dan saran strategis untuk pengelolaan keuangan yang lebih baik. Gunakan bahasa yang profesional namun mudah dipahami. Maksimal 2-3 kalimat pendek.
"""
        }
        
        responses = {}
        
        # Determine which tones to generate
        if tone_type == "all":
            tones_to_generate = tone_prompts.keys()
        elif tone_type in tone_prompts:
            tones_to_generate = [tone_type]
        else:
            raise ValueError(f"Invalid tone_type: {tone_type}. Must be one of: {list(tone_prompts.keys())} or 'all'")
        
        # Generate responses for each tone
        for tone in tones_to_generate:
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
                            {"role": "user", "content": tone_prompts[tone]}
                        ]
                    }
                )
                response.raise_for_status()
                data = response.json()
                responses[tone] = data['choices'][0]['message']['content']
                
            except requests.exceptions.RequestException as e:
                print(f"Error generating {tone} response: {e}")
                responses[tone] = f"Gagal menghasilkan respons untuk tone {tone}"
            except (KeyError, IndexError) as e:
                print(f"Invalid API response structure for {tone}: {e}")
                responses[tone] = f"Format respons tidak valid untuk tone {tone}"
        
        return responses

openrouter_service = OpenRouterService()