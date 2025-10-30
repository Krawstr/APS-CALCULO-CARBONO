from flask import Flask
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import os

from routes.routes import routes as main_routes

def create_app():
    """Cria e configura uma instância da aplicação Flask."""
    
    load_dotenv()

    app = Flask(__name__)
    
    app.secret_key = os.urandom(24) 
    CORS(app)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Erro: A variável de ambiente GOOGLE_API_KEY não foi definida.")
    else:
        try:
            genai.configure(api_key=api_key)
        except Exception as e:
            print(f"Erro ao configurar a API do Google: {e}")

    app.register_blueprint(main_routes)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=True)