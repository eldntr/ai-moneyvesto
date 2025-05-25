# app/__init__.py
from flask import Flask
from flask_cors import CORS

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    CORS(app)  

    # Impor dan daftarkan blueprint
    from .routes import chat_bp
    app.register_blueprint(chat_bp)

    return app