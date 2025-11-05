"""
Microsserviço de Perfil
Responsável por: visualização e edição de perfil, upload de foto
"""
import os
from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
from src.models import db, User
from routes import routes


def allowed_file(filename):
    """Valida extensão de arquivo"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@routes.route('/profile')
@login_required
def profile():
    """Página de perfil"""
    return render_template('profile.html', user=current_user)


@routes.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Atualiza perfil"""
    try:
        data = request.form
        
        # Atualizar email
        new_email = data.get('email')
        if new_email and new_email != current_user.email:
            if User.query.filter_by(email=new_email).first():
                return jsonify({"error": "Email já em uso"}), 400
            current_user.email = new_email
        
        # Atualizar senha
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if new_password:
            if not current_password:
                return jsonify({"error": "Senha atual obrigatória"}), 400
            if not current_user.check_password(current_password):
                return jsonify({"error": "Senha incorreta"}), 400
            current_user.set_password(new_password)
        
        # Upload de foto
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                file.save(filepath)
                
                if current_user.profile_picture != 'default_avatar.png':
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_picture)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                current_user.profile_picture = unique_filename
        
        db.session.commit()
        return jsonify({"message": "Perfil atualizado!"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro: {e}")
        return jsonify({"error": "Erro ao atualizar"}), 500


@routes.route('/profile/delete-picture', methods=['POST'])
@login_required
def delete_profile_picture():
    """Remove foto de perfil"""
    try:
        if current_user.profile_picture != 'default_avatar.png':
            old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_picture)
            if os.path.exists(old_path):
                os.remove(old_path)
            current_user.profile_picture = 'default_avatar.png'
            db.session.commit()
        return jsonify({"message": "Foto removida"}), 200
    except Exception as e:
        return jsonify({"error": "Erro"}), 500
