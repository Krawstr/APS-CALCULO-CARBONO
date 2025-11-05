"""
Microsserviço de Autenticação
Responsável por: login, registro, logout
"""
from flask import render_template, request, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from src.models import db, User
from routes import routes


@routes.route('/register', methods=['GET', 'POST'])
def register():
    """Cadastro de novos usuários"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validações
        if not username or not email or not password:
            return jsonify({"error": "Todos os campos são obrigatórios"}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Nome de usuário já existe"}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email já cadastrado"}), 400
        
        # Criar novo usuário
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"message": "Usuário cadastrado com sucesso!"}), 201
    
    return render_template('register.html')


@routes.route('/login', methods=['GET', 'POST'])
def login():
    """Login de usuários"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Usuário e senha são obrigatórios"}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({"error": "Usuário ou senha incorretos"}), 401
        
        login_user(user)
        return jsonify({
            "message": "Login realizado com sucesso!",
            "username": user.username
        }), 200
    
    return render_template('login.html')


@routes.route('/logout')
@login_required
def logout():
    """Logout de usuários"""
    logout_user()
    return redirect(url_for('main.login'))
