# app/routes.py

from flask import Blueprint, request, jsonify
from app.services.openrouter_service import openrouter_service
from PIL import Image
import io

chat_bp = Blueprint('chat_bp', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@chat_bp.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    previous_chats = request.json.get('previous_chats', [])  # Default to an empty list if not provided

    if not user_message:
        return jsonify({"error": "Pesan tidak boleh kosong"}), 400

    if not isinstance(previous_chats, list):
        return jsonify({"error": "previous_chats harus berupa array JSON"}), 400

    try:
        model_response = openrouter_service.get_chat_response(user_message, previous_chats)
        return jsonify({"response": model_response})
    except (ConnectionError, ValueError) as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route('/vision', methods=['POST'])
def vision():
    if 'image' not in request.files:
        return jsonify({"error": "File gambar tidak ditemukan"}), 400
    
    text_prompt = request.form.get('message')
    if not text_prompt:
        return jsonify({"error": "Pesan teks tidak ditemukan"}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "Tidak ada file gambar yang dipilih"}), 400

    if image_file and allowed_file(image_file.filename):
        try:
            image = Image.open(io.BytesIO(image_file.read()))
            image_format = image.format or 'JPEG' 
            image.seek(0)
            
            model_response = openrouter_service.get_vision_response(text_prompt, image, image_format)
            return jsonify({"response": model_response})
        except (ConnectionError, ValueError) as e:
            return jsonify({"error": str(e)}), 500
        except Exception as e:
            return jsonify({"error": f"Gagal memproses gambar: {str(e)}"}), 400
    
    return jsonify({"error": "Jenis file tidak diizinkan"}), 400

@chat_bp.route('/record', methods=['POST'])
def record_finance_route():
    """
    Endpoint untuk memproses pencatatan transaksi dari pesan teks.
    """
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "Pesan tidak boleh kosong"}), 400

    try:
        # Panggil service baru untuk memproses transaksi
        result = openrouter_service.record_finance(user_message)
        return jsonify(result)
    except (ConnectionError, ValueError) as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        # Menangkap error tak terduga lainnya
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500