import os
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
import google.generativeai as genai
from dotenv import load_dotenv

from src.models import db, User
from routes.routes import routes as main_routes

# Configuração de upload
UPLOAD_FOLDER = 'static/uploads/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def create_app():
    load_dotenv()
    
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave-super-secreta-mude-isso')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB
    
    # IMPORTANTE: Criar pasta de uploads se não existir
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    print(f"✅ Pasta de uploads criada/verificada: {UPLOAD_FOLDER}")
    
    CORS(app)
    
    # Inicializar banco de dados
    db.init_app(app)
    
    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️ Erro: A variável GOOGLE_API_KEY não foi definida.")
    else:
        try:
            genai.configure(api_key=api_key)
            print("✅ Google Gemini API configurada")
        except Exception as e:
            print(f"❌ Erro ao configurar a API do Google: {e}")
    
    # Registrar blueprints
    app.register_blueprint(main_routes)
    
    # Criar tabelas do banco de dados
    with app.app_context():
        db.create_all()
        print("✅ Banco de dados inicializado!")
    
    return app

if __name__ == "__main__":
    app = create_app()
    print("🚀 Servidor Flask iniciando...")
    app.run(host="127.0.0.1", port=5000, debug=True)
