from src.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """Model para usuários autenticados"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com histórico de chats
    chat_histories = db.relationship('ChatHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Cria hash seguro da senha"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class ChatHistory(db.Model):
    """Model para histórico de conversas"""
    __tablename__ = 'chat_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Dados da conversa
    conversation_log = db.Column(db.Text, nullable=True)  # JSON string
    extracted_data = db.Column(db.Text, nullable=True)     # JSON string
    report_results = db.Column(db.Text, nullable=True)     # JSON string
    report_narrative = db.Column(db.Text, nullable=True)   # Texto do relatório
    
    def __repr__(self):
        return f'<ChatHistory {self.id} - User {self.user_id}>'
