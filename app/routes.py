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

    # Tambahkan prompt untuk memberi tahu model
    text_prompt += """
    Tolong analisis gambar yang diberikan. Jika itu adalah foto nota, ekstrak informasi transaksi seperti deskripsi barang, jumlah, dan harga. 
    Jika itu adalah foto barang, maka cari harga jika tidak ada maka buat deskripsi singkat tentang barang tersebut. 
    Jika itu adalah aktivitas rekening, tambahkan informasi apakah itu pengeluaran atau pemasukan untuk setiap aktivitas aktivitasnya.
    """

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

@chat_bp.route('/transaction', methods=['POST'])
def process_transaction_image():
    """
    Endpoint untuk memproses gambar nota/struk menjadi data transaksi terstruktur.
    Menggabungkan vision processing, finance recording, dan respons dengan berbagai nada.
    """
    if 'image' not in request.files:
        return jsonify({"error": "File gambar tidak ditemukan"}), 400
    
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({"error": "Tidak ada file gambar yang dipilih"}), 400

    if not (image_file and allowed_file(image_file.filename)):
        return jsonify({"error": "Jenis file tidak diizinkan"}), 400

    # Get optional message from the form for context
    user_message = request.form.get('message', '')
    
    # Get tone type parameter (optional, defaults to "all")
    tone_type = request.form.get('tone_type', 'all')

    # Prompt khusus untuk ekstraksi transaksi dari gambar
    base_prompt = """
    Analisis gambar ini dan ekstrak semua informasi transaksi yang terlihat atau disebutkan. 
    Berikan hasil dalam format teks yang menjelaskan setiap item yang dibeli, jumlahnya, dan harganya.
    Format seperti: "beli [nama barang] [jumlah] dengan harga [harga]" untuk setiap item.
    Jika ada beberapa item, pisahkan dengan kalimat terpisah.
    Fokus pada nama barang, kuantitas, dan harga total per item.
    """

    # Gabungkan pesan pengguna dengan prompt dasar untuk memberikan konteks tambahan ke VLM
    final_prompt = f"{user_message}\n\n{base_prompt}".strip()

    try:
        # Step 1: Process image with vision service
        image = Image.open(io.BytesIO(image_file.read()))
        image_format = image.format or 'JPEG'
        
        vision_response = openrouter_service.get_vision_response(
            final_prompt, image, image_format
        )
        
        # Step 2: Process vision response with record service
        structured_transactions = openrouter_service.record_finance(vision_response)
        
        # Step 3: Generate tone-based responses
        tone_responses = openrouter_service.get_tone_responses(vision_response, structured_transactions, tone_type)
        
        return jsonify({
            "vision_analysis": vision_response,
            "transactions": structured_transactions,
            "responses": tone_responses
        })
        
    except (ConnectionError, ValueError) as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": f"Gagal memproses transaksi dari gambar: {str(e)}"}), 500