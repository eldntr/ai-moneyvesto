# app/routes.py
from flask import Blueprint, request, jsonify
from app.services.openrouter_service import openrouter_service

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    """Endpoint untuk menerima pesan dan mengembalikan respons dari LLM."""
    user_message = request.json.get('message')

    if not user_message:
        return jsonify({"error": "Pesan tidak boleh kosong"}), 400

    try:
        model_response = openrouter_service.get_chat_response(user_message)
        return jsonify({"response": model_response})
    except (ConnectionError, ValueError) as e:
        return jsonify({"error": str(e)}), 500