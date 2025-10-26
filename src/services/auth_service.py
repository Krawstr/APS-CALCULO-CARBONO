from src.extensions import db
from src.models import User
from flask import session


def register_user(username, email, password):
    """
    Registra um novo usuário no sistema.
    
    Args:
        username (str): Nome de usuário único
        email (str): Email único
        password (str): Senha em texto plano (será hasheada)
    
    Returns:
        tuple: (success: bool, message: str, user: User|None)
    """
    try:
        # Verifica se username já existe
        if User.query.filter_by(username=username).first():
            return False, "Nome de usuário já está em uso.", None
        
        # Verifica se email já existe
        if User.query.filter_by(email=email).first():
            return False, "Email já está cadastrado.", None
        
        # Cria novo usuário
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return True, "Usuário registrado com sucesso!", new_user
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar usuário: {e}")
        return False, f"Erro ao registrar: {str(e)}", None


def login_user(username_or_email, password):
    """
    Autentica um usuário e cria sessão.
    
    Args:
        username_or_email (str): Username ou email
        password (str): Senha em texto plano
    
    Returns:
        tuple: (success: bool, message: str, user: User|None)
    """
    try:
        # Busca usuário por username ou email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        if not user:
            return False, "Usuário ou senha incorretos.", None
        
        # Verifica senha
        if not user.check_password(password):
            return False, "Usuário ou senha incorretos.", None
        
        # Cria sessão do usuário
        session['user_id'] = user.id
        session['username'] = user.username
        session.permanent = True  # Mantém sessão mesmo após fechar navegador
        
        return True, "Login realizado com sucesso!", user
        
    except Exception as e:
        print(f"Erro ao fazer login: {e}")
        return False, f"Erro ao fazer login: {str(e)}", None


def logout_user():
    """Remove dados do usuário da sessão"""
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('conversation_history', None)
    session.pop('report_data', None)


def get_current_user():
    """
    Retorna o usuário atualmente autenticado.
    
    Returns:
        User|None: Objeto User ou None se não autenticado
    """
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None


def is_authenticated():
    """Verifica se existe um usuário autenticado na sessão"""
    return 'user_id' in session
