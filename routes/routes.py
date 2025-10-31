import os
import json
import re
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app
import google.generativeai as genai
from services import carbon_calculator as carbon_calculator
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from src.models import db, User, Report
from datetime import datetime
from flask import current_app



routes = Blueprint('main', __name__)

conversation_history = []

SYSTEM_PROMPT = """
Você é a Dalva Carlinhos, uma assistente virtual amigável e especialista em sustentabilidade.
Seu objetivo é guiar o usuário para calcular sua pegada de carbono mensal.
Faça as perguntas de forma clara e uma de cada vez. Seja direto.
Siga estritamente esta ordem de coleta de informações:
1. Transporte:
   - Se o usuário confirmar que tem carro, pergunte o tipo de combustível (gasolina, etanol, diesel).
   - Depois, pergunte a média de quilômetros rodados por mês.
   - Após o transporte individual, pergunte sobre o uso de transporte público (ônibus/metrô) e a média de km/mês.
2. Energia em Casa:
   - Pergunte o consumo médio mensal de eletricidade em kWh.
   - Pergunte sobre o uso de gás de cozinha (ex: quantos botijões de 13kg você utiliza por mês?).

Mantenha as respostas curtas e focadas.
Quando tiver coletado todos os dados, diga EXATAMENTE: "Excelente! Tenho todas as informações que preciso. Podemos gerar seu relatório?"
"""


@routes.route("/")
@login_required
def home():
    return render_template("index.html", username=current_user.username)


@routes.route("/start_conversation", methods=['POST'])
@login_required 
def start_conversation():
    global conversation_history
    conversation_history = [
        {'role': 'user', 'parts': [SYSTEM_PROMPT]},
        {'role': 'model', 'parts': ["Olá! Eu sou Dalva Carlinhos, sua assistente para cálculo de pegada de carbono. Você possui carro?"]}
    ]
    return jsonify({"response": conversation_history[-1]['parts'][0]})


@routes.route("/send_message", methods=['POST'])
@login_required  
def send_message():
    global conversation_history
    message = request.get_json()
    if not message or 'text' not in message:
        return jsonify({"error": "Mensagem inválida"}), 400

    user_text = message['text']
    conversation_history.append({'role': 'user', 'parts': [user_text]})

    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(conversation_history)
    assistant_response = response.text
    
    conversation_history.append({'role': 'model', 'parts': [assistant_response]})
    return jsonify({"response": assistant_response})


@routes.route("/generate_report", methods=['POST'])
@login_required
def generate_report():
    global conversation_history
    
    extraction_prompt = f"""
    Analise a seguinte conversa e extraia os dados para o cálculo da pegada de carbono. A conversa é: {json.dumps(conversation_history)}
    Sua resposta DEVE SER APENAS um objeto JSON, sem nenhum texto adicional. Use as seguintes chaves: "km_carro", "tipo_combustivel", "km_onibus", "kwh_eletricidade", "kg_gas_glp".
    Para "tipo_combustivel", use um dos seguintes valores: "gasolina", "etanol", "diesel". Se uma informação não foi fornecida, use o valor null.
    Para valores numéricos, extraia APENAS o número (ex: "1 botijao" -> 13, "600km" -> 600).
    """
    
    try:
        # --- CORREÇÃO 1: Nome do modelo corrigido ---
        model = genai.GenerativeModel('gemini-2.0-flash') 
        
        # --- CORREÇÃO 2: Bloco try/except para a chamada da API ---
        response_json_str = model.generate_content(extraction_prompt).text
        
    except Exception as e:
        # Captura erros da API (modelo inválido, chave errada, etc.)
        print(f"Erro na API Gemini (Extração): {e}")
        return jsonify({"error": "Não foi possível contatar a IA para extrair dados."}), 500

    extracted_data = {}
    try:
        match = re.search(r'\{.*\}', response_json_str, re.DOTALL)
        if match:
            clean_json_str = match.group(0)
            extracted_data = json.loads(clean_json_str)
        else:
            raise json.JSONDecodeError("Nenhum JSON encontrado na resposta", response_json_str, 0)
    except json.JSONDecodeError as e:
        print(f"Erro de JSON Decode: {e}")
        # Retorna o erro que você já tinha, o que é ótimo
        return jsonify({"error": "Não foi possível extrair os dados da conversa."}), 500

    # ... (Seu código de sanitização de dados continua aqui) ...
    # (O código de sanitização parece correto)
    sanitized_data = {}
    for key, value in extracted_data.items():
        if value is None:
            sanitized_data[key] = None
            continue
            
        if key == 'tipo_combustivel':
            sanitized_data[key] = str(value) if value else None
        else:
            try:
                numeric_value_str = re.sub(r'[^\d.]', '', str(value))
                if numeric_value_str:
                    if key == 'kg_gas_glp' and float(numeric_value_str) <= 5: 
                        sanitized_data[key] = float(numeric_value_str) * 13.0
                    else:
                        sanitized_data[key] = float(numeric_value_str)
                else:
                    sanitized_data[key] = None
            except (ValueError, TypeError):
                sanitized_data[key] = None

    calculation_results = carbon_calculator.calculate_footprint(sanitized_data)

    report_prompt = f"""
    Com base nos seguintes resultados do cálculo da pegada de carbono de um usuário (em kg de CO2e): {json.dumps(calculation_results)}
    Gere um relatório personalizado, amigável e otimista.
    - Comece com um resumo do resultado total.
    - Analise qual categoria foi a maior emissora.
    - Ofereça 3 dicas práticas e acionáveis para o usuário reduzir sua pegada, focando na categoria de maior impacto.
    - Termine com uma mensagem de encorajamento.
    """

    try:
        # --- CORREÇÃO 3: Bloco try/except para a SEGUNDA chamada da API ---
        text_report = model.generate_content(report_prompt).text
        
    except Exception as e:
        # Captura erros da API (segurança, cota, etc.)
        print(f"Erro na API Gemini (Geração de Relatório): {e}")
        # Mesmo que a extração funcione, a geração do relatório pode falhar
        # Podemos decidir continuar e salvar NULL ou retornar um erro.
        # Vamos retornar um erro para o usuário saber.
        return jsonify({"error": "Os dados foram calculados, mas falhamos ao gerar o relatório narrativo."}), 500

    
    # ... (Seu código de salvar no DB continua aqui) ...
    # (Parece correto)
    try:
        new_report = Report(
            user_id=current_user.id,
            km_carro=sanitized_data.get('km_carro'),
            tipo_combustivel=sanitized_data.get('tipo_combustivel'),
            km_onibus=sanitized_data.get('km_onibus'),
            kwh_eletricidade=sanitized_data.get('kwh_eletricidade'),
            kg_gas_glp=sanitized_data.get('kg_gas_glp'),
            total_kg_co2e=calculation_results['total_kg_co2e'],
            transporte_kg_co2e=calculation_results['details_kg_co2e']['transporte'],
            energia_eletrica_kg_co2e=calculation_results['details_kg_co2e']['energia_eletrica'],
            gas_cozinha_kg_co2e=calculation_results['details_kg_co2e']['gas_cozinha'],
            narrative_report=text_report
        )
        
        db.session.add(new_report)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar no Banco de Dados: {e}")
        return jsonify({"error": "Erro ao salvar o relatório no banco de dados."}), 500

    
    final_response = {
        "data_for_dashboard": calculation_results,
        "narrative_report": text_report,
        "report_id": new_report.id 
    }

    session['report_data'] = final_response
    return jsonify({"status": "success", "redirect_url": url_for('main.show_report')})


@routes.route("/report")
def show_report():
    report_data = session.get('report_data', None)
    if not report_data:
        return redirect(url_for('main.home')) # Nota: 'main.home'
    return render_template("calculator.html", report_data=report_data)


@routes.route('/calculator')
def show_calculator_form():
    return render_template('direct_calculator.html')


@routes.route('/calculator', methods=['POST'])
@login_required
def handle_calculator_form():
    sanitized_data = {
        'km_carro': request.form.get('km_carro', type=float),
        'tipo_combustivel': request.form.get('tipo_combustivel'),
        'km_onibus': request.form.get('km_onibus', type=float),
        'kwh_eletricidade': request.form.get('kwh_eletricidade', type=float),
        'kg_gas_glp': (request.form.get('botijoes_gas', type=float) or 0) * 13.0
    }
    
    if not sanitized_data['tipo_combustivel']:
        sanitized_data['tipo_combustivel'] = None

    calculation_results = carbon_calculator.calculate_footprint(sanitized_data)

    report_prompt = f"""
    Com base nos seguintes resultados do cálculo da pegada de carbono de um usuário (em kg de CO2e): {json.dumps(calculation_results)}
    Gere um relatório personalizado, amigável e otimista. Analise a maior fonte de emissão e ofereça 3 dicas práticas para reduzi-la. Termine com uma mensagem de encorajamento.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    text_report = model.generate_content(report_prompt).text
    
    # NOVO: Salvar relatório no banco de dados
    new_report = Report(
        user_id=current_user.id,
        km_carro=sanitized_data.get('km_carro'),
        tipo_combustivel=sanitized_data.get('tipo_combustivel'),
        km_onibus=sanitized_data.get('km_onibus'),
        kwh_eletricidade=sanitized_data.get('kwh_eletricidade'),
        kg_gas_glp=sanitized_data.get('kg_gas_glp'),
        total_kg_co2e=calculation_results['total_kg_co2e'],
        transporte_kg_co2e=calculation_results['details_kg_co2e']['transporte'],
        energia_eletrica_kg_co2e=calculation_results['details_kg_co2e']['energia_eletrica'],
        gas_cozinha_kg_co2e=calculation_results['details_kg_co2e']['gas_cozinha'],
        narrative_report=text_report
    )
    
    db.session.add(new_report)
    db.session.commit()
    
    final_response = {
        "data_for_dashboard": calculation_results,
        "narrative_report": text_report,
        "report_id": new_report.id
    }

    session['report_data'] = final_response
    return redirect(url_for('main.show_report'))

@routes.route('/register', methods=['GET', 'POST'])
def register():
    """Rota para cadastro de novos usuários"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validações
        if not username or not email or not password:
            return jsonify({"error": "Todos os campos são obrigatórios"}), 400
        
        # Verificar se usuário já existe
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
    """Rota para login de usuários"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Usuário e senha são obrigatórios"}), 400
        
        # Buscar usuário
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({"error": "Usuário ou senha incorretos"}), 401
        
        # Fazer login
        login_user(user)
        return jsonify({
            "message": "Login realizado com sucesso!",
            "username": user.username
        }), 200
    
    return render_template('login.html')

@routes.route('/logout')
@login_required
def logout():
    """Rota para logout"""
    logout_user()
    return redirect(url_for('main.login'))

@routes.route('/history')
@login_required
def view_history():
    """Exibe o histórico de relatórios do usuário"""
    reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
    return render_template('history.html', reports=reports)


@routes.route('/api/reports')
@login_required
def get_user_reports():
    """API para obter relatórios do usuário (formato JSON)"""
    reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.created_at.desc()).all()
    return jsonify([report.to_dict() for report in reports])


@routes.route('/report/<int:report_id>')
@login_required
def view_specific_report(report_id):
    """Visualiza um relatório específico"""
    report = Report.query.filter_by(id=report_id, user_id=current_user.id).first_or_404()
    
    report_data = {
        "data_for_dashboard": {
            'details_kg_co2e': {
                'transporte': report.transporte_kg_co2e,
                'energia_eletrica': report.energia_eletrica_kg_co2e,
                'gas_cozinha': report.gas_cozinha_kg_co2e
            },
            'total_kg_co2e': report.total_kg_co2e
        },
        "narrative_report": report.narrative_report
    }
    
    return render_template('calculator.html', report_data=report_data)


@routes.route('/report/delete/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    """Deleta um relatório específico"""
    report = Report.query.filter_by(id=report_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(report)
    db.session.commit()
    
    return jsonify({"message": "Relatório deletado com sucesso"}), 200

# Função auxiliar para validar extensões de arquivo
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Rota para visualizar perfil
@routes.route('/profile')
@login_required
def profile():
    """Página de perfil do usuário"""
    return render_template('profile.html', user=current_user)

# Rota para atualizar perfil
@routes.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Atualiza informações do perfil"""
    try:
        data = request.form
        
        # Atualizar email
        new_email = data.get('email')
        if new_email and new_email != current_user.email:
            # Verificar se email já existe
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user:
                return jsonify({"error": "Este email já está em uso"}), 400
            current_user.email = new_email
        
        # Atualizar senha
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if new_password:
            if not current_password:
                return jsonify({"error": "Senha atual é obrigatória"}), 400
            
            # Verificar senha atual
            if not current_user.check_password(current_password):
                return jsonify({"error": "Senha atual incorreta"}), 400
            
            # Atualizar senha
            current_user.set_password(new_password)
        
        # Upload de foto de perfil
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename and allowed_file(file.filename):
                # Gerar nome único para o arquivo
                filename = secure_filename(file.filename)
                unique_filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Salvar arquivo
                file.save(filepath)
                
                # Deletar foto antiga se não for a padrão
                if current_user.profile_picture != 'default_avatar.png':
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_picture)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                
                # Atualizar no banco
                current_user.profile_picture = unique_filename
        
        db.session.commit()
        return jsonify({"message": "Perfil atualizado com sucesso!"}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao atualizar perfil: {e}")
        return jsonify({"error": "Erro ao atualizar perfil"}), 500

# Rota para deletar foto de perfil
@routes.route('/profile/delete-picture', methods=['POST'])
@login_required
def delete_profile_picture():
    """Remove a foto de perfil do usuário"""
    try:
        if current_user.profile_picture != 'default_avatar.png':
            old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_picture)
            if os.path.exists(old_path):
                os.remove(old_path)
            
            current_user.profile_picture = 'default_avatar.png'
            db.session.commit()
        
        return jsonify({"message": "Foto de perfil removida"}), 200
    except Exception as e:
        return jsonify({"error": "Erro ao remover foto"}), 500