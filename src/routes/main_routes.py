from flask import (
    Blueprint, render_template, request, jsonify, session, 
    redirect, url_for, flash
)
from functools import wraps

# Importa as NOSSAS funções dos serviços
from src.services import chatbot_service
from src.services import carbon_calculator
from src.services import history_service
from src.services import auth_service
import json


routes = Blueprint('main', __name__)


# ============================================
# DECORADOR PARA PROTEGER ROTAS
# ============================================
def login_required(f):
    """Decorador para proteger rotas que exigem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth_service.is_authenticated():
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# ROTAS DE AUTENTICAÇÃO
# ============================================

@routes.route("/")
def home():
    """Página inicial - redireciona para login ou dashboard"""
    if auth_service.is_authenticated():
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))


@routes.route("/register", methods=['GET', 'POST'])
def register():
    """Página de registro de novos usuários"""
    if auth_service.is_authenticated():
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validações básicas
        if not username or not email or not password:
            flash('Todos os campos são obrigatórios.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('As senhas não coincidem.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return render_template('register.html')
        
        # Tenta registrar
        success, message, user = auth_service.register_user(username, email, password)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('main.login'))
        else:
            flash(message, 'danger')
            return render_template('register.html')
    
    return render_template('register.html')


@routes.route("/login", methods=['GET', 'POST'])
def login():
    """Página de login"""
    if auth_service.is_authenticated():
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')
        
        if not username_or_email or not password:
            flash('Preencha todos os campos.', 'danger')
            return render_template('login.html')
        
        # Tenta fazer login
        success, message, user = auth_service.login_user(username_or_email, password)
        
        if success:
            flash(f'Bem-vindo, {user.username}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(message, 'danger')
            return render_template('login.html')
    
    return render_template('login.html')


@routes.route("/logout")
def logout():
    """Faz logout do usuário"""
    auth_service.logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('main.login'))


# ============================================
# DASHBOARD E CHATBOT 
# ============================================


@routes.route("/dashboard")
@login_required
def dashboard():
    """Dashboard principal após login"""
    user = auth_service.get_current_user()
    return render_template("dashboard.html", user=user)

@routes.route("/chat")
@login_required
def show_chat():
    """Página do chatbot"""
    user = auth_service.get_current_user()
    return render_template("index.html", user=user)

@routes.route("/start_conversation", methods=['POST'])
@login_required
def start_conversation():
    """Inicia uma nova conversa com o chatbot"""
    conversation_history = chatbot_service.initialize_chat()
    session['conversation_history'] = conversation_history
    return jsonify({"response": conversation_history[-1]['parts'][0]})


@routes.route("/send_message", methods=['POST'])
@login_required
def send_message():
    """Envia mensagem para o chatbot"""
    conversation_history = session.get('conversation_history')
    if not conversation_history:
        return jsonify({"error": "Conversa não iniciada"}), 400

    message = request.get_json()
    if not message or 'text' not in message:
        return jsonify({"error": "Mensagem inválida"}), 400

    assistant_response, updated_history = chatbot_service.continue_chat(
        conversation_history, 
        message['text']
    )
    
    session['conversation_history'] = updated_history
    return jsonify({"response": assistant_response})


@routes.route("/generate_report", methods=['POST'])
@login_required
def generate_report():
    """Gera relatório de pegada de carbono"""
    conversation_history = session.get('conversation_history')
    user = auth_service.get_current_user()
    
    if not conversation_history or not user:
        return jsonify({"error": "Sessão inválida ou conversa não encontrada"}), 400

    # 1. Extrair dados
    extracted_data = chatbot_service.extract_data_from_chat(conversation_history)
    if extracted_data is None:
        return jsonify({"error": "Não foi possível extrair os dados da conversa."}), 500

    # 2. Calcular pegada
    calculation_results = carbon_calculator.calculate_footprint(extracted_data)

    # 3. Gerar relatório narrativo
    text_report = chatbot_service.generate_narrative_report(calculation_results)
    
    # 4. Preparar resposta final
    final_response = {
        "data_for_dashboard": calculation_results,
        "narrative_report": text_report,
    }

    # 5. Salvar no histórico
    history_service.save_chat_to_history(
        user_id=user.id,
        history_log=conversation_history,
        extracted_data=extracted_data,
        results=calculation_results,
        narrative=text_report
    )

    session['report_data'] = final_response
    session.pop('conversation_history', None) 
    
    return jsonify({"status": "success", "redirect_url": url_for('main.show_report')})


@routes.route("/report")
@login_required
def show_report():
    """Mostra o relatório gerado"""
    report_data = session.get('report_data', None)
    if not report_data:
        return redirect(url_for('main.dashboard'))
    return render_template("calculator.html", report_data=report_data)


@routes.route('/calculator')
@login_required
def show_calculator_form():
    """Formulário de cálculo direto"""
    return render_template('direct_calculator.html')


@routes.route('/calculator', methods=['POST'])
@login_required
def handle_calculator_form():
    """Processa formulário de cálculo direto"""
    user = auth_service.get_current_user()
    
    # 1. Extrair dados do formulário
    sanitized_data = {
        'km_carro': request.form.get('km_carro', type=float),
        'tipo_combustivel': request.form.get('tipo_combustivel') or None,
        'km_onibus': request.form.get('km_onibus', type=float),
        'kwh_eletricidade': request.form.get('kwh_eletricidade', type=float),
        'kg_gas_glp': (request.form.get('botijoes_gas', type=float) or 0) * 13.0
    }

    # 2. Calcular pegada
    calculation_results = carbon_calculator.calculate_footprint(sanitized_data)

    # 3. Gerar relatório
    text_report = chatbot_service.generate_narrative_report(calculation_results)
    
    # 4. Preparar resposta final
    final_response = {
        "data_for_dashboard": calculation_results,
        "narrative_report": text_report,
    }
    
    # 5. Salvar no histórico (ATUALIZADO: usa user.id)
    history_service.save_chat_to_history(
        user_id=user.id,
        history_log=None,
        extracted_data=sanitized_data,
        results=calculation_results,
        narrative=text_report
    )

    session['report_data'] = final_response
    return redirect(url_for('main.show_report'))


# ============================================
# HISTÓRICO DE CONVERSAS
# ============================================

@routes.route("/history")
@login_required
def show_history():
    """Mostra histórico de conversas do usuário"""
    user = auth_service.get_current_user()
    history = history_service.get_user_history(user.id, limit=20)
    return render_template('history.html', history=history, user=user)


@routes.route("/history/<int:chat_id>")
@login_required
def view_chat(chat_id):
    """Visualiza uma conversa específica do histórico"""
    user = auth_service.get_current_user()
    chat = history_service.get_chat_by_id(chat_id, user.id)
    
    if not chat:
        flash('Conversa não encontrada.', 'danger')
        return redirect(url_for('main.show_history'))
    
    # Parse dos dados JSON
    report_data = {
        "data_for_dashboard": json.loads(chat.report_results) if chat.report_results else {},
        "narrative_report": chat.report_narrative
    }
    
    return render_template('calculator.html', report_data=report_data)


@routes.route("/history/<int:chat_id>/delete", methods=['POST'])
@login_required
def delete_chat(chat_id):
    """Deleta uma conversa do histórico"""
    user = auth_service.get_current_user()
    success, message = history_service.delete_chat(chat_id, user.id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('main.show_history'))

@routes.route("/api/history", methods=['GET'])
@login_required
def get_user_history_api():
    """API para buscar histórico de conversas (para sidebar)"""
    user = auth_service.get_current_user()
    limit = request.args.get('limit', 10, type=int)
    history = history_service.get_user_history(user.id, limit=limit)
    
    # Formata os dados para o frontend
    history_data = []
    for chat in history:
        history_data.append({
            'id': chat.id,
            'created_at': chat.created_at.strftime('%d/%m/%Y às %H:%M'),
            'created_short': chat.created_at.strftime('%d/%m'),
            'has_conversation': chat.conversation_log is not None
        })
    
    return jsonify(history_data)


@routes.route("/api/clear_conversation", methods=['POST'])
@login_required
def clear_current_conversation():
    """Limpa a conversa atual da sessão"""
    session.pop('conversation_history', None)
    session.pop('report_data', None)
    return jsonify({"status": "success"})