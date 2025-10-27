import os
from flask import Flask
from flask_cors import CORS 
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import timedelta

# Importa as nossas extensões
from .extensions import db 

def create_app():
    """
    Função "Fábrica" para criar a aplicação Flask.
    """
    
    # Carrega as variáveis de ambiente do ficheiro .env
    load_dotenv() 

    # Cria a instância da aplicação
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates',
                instance_relative_config=True)

    # --- Configurações da Aplicação ---

    # 1. Chave Secreta (IMPORTANTE)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'uma-chave-secreta-de-fallback')
    
    # 2. Sessão permanente (mantém login por 7 dias)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # 3. Configuração da Base de Dados
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 
        'sqlite:///' + os.path.join(app.instance_path, 'project.db'))
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Garante que a pasta 'instance/' existe
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    # 4. Configuração da API do Gemini
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ Erro: A variável de ambiente GEMINI_API_KEY não foi definida.")
    else:
        try:
            genai.configure(api_key=api_key)
            print("✅ API Gemini configurada com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao configurar a API do Gemini: {e}")

    # --- Inicializar Extensões ---
    
    # 5. Inicializa o CORS (Cross-Origin Resource Sharing)
    CORS(app)
    
    # 6. Inicializa a Base de Dados
    db.init_app(app)
    
    # ⚠️ ADICIONE ESTA LINHA AQUI (IMPORTANTE!)
    from . import models  # Garante que os models são registrados
    
    # --- Registar Blueprints (Rotas) ---
    from .routes.main_routes import routes as main_blueprint
    app.register_blueprint(main_blueprint)

    # --- Comandos CLI ---
    @app.cli.command("init-db")
    def init_db_command():
        """Cria as tabelas da base de dados."""
        with app.app_context():
            db.create_all()
            print("✅ Base de dados inicializada!")
    

    
    @app.cli.command("create-admin")
    def create_admin_command():
        """Cria um usuário admin para testes."""
        from .models import User
        with app.app_context():
            admin = User(username='admin', email='admin@carbonbot.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário admin criado! (username: admin, senha: admin123)")
        
    return app
