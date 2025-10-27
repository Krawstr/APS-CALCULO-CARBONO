from flask import (
    Blueprint, render_template, request, jsonify, session, 
    redirect, url_for
)
from src.services import chatbot_service, carbon_calculator

# Cria o Blueprint
routes = Blueprint('main', __name__)


@routes.route("/")
def home():
    return render_template("index.html")


@routes.route("/start_conversation", methods=['POST'])
def start_conversation():
    # Chama o serviço para iniciar a conversa
    conversation_history = chatbot_service.initialize_chat()
    
    # Guarda o histórico na sessão do utilizador
    session['conversation_history'] = conversation_history
    
    # Retorna a primeira mensagem
    return jsonify({"response": conversation_history[-1]['parts'][0]})


@routes.route("/send_message", methods=['POST'])
def send_message():
    # Obtém o histórico ATUAL da sessão
    conversation_history = session.get('conversation_history')
    if not conversation_history:
        return jsonify({"error": "Conversa não iniciada"}), 400

    message = request.get_json()
    if not message or 'text' not in message:
        return jsonify({"error": "Mensagem inválida"}), 400

    # Chama o serviço para obter a resposta
    assistant_response, updated_history = chatbot_service.continue_chat(
        conversation_history, 
        message['text']
    )
    
    # Atualiza o histórico na sessão
    session['conversation_history'] = updated_history
    
    return jsonify({"response": assistant_response})


@routes.route("/generate_report", methods=['POST'])
def generate_report():
    # Obtém o histórico final da sessão
    conversation_history = session.get('conversation_history')
    if not conversation_history:
        return jsonify({"error": "Conversa não encontrada"}), 400

    # 1. Extrair dados usando o serviço de chatbot
    extracted_data = chatbot_service.extract_data_from_chat(conversation_history)
    if extracted_data is None:
        return jsonify({"error": "Não foi possível extrair os dados da conversa."}), 500

    # 2. Calcular pegada usando o serviço de calculadora
    calculation_results = carbon_calculator.calculate_footprint(extracted_data)

    # 3. Gerar relatório narrativo usando o serviço de chatbot
    text_report = chatbot_service.generate_narrative_report(calculation_results)
    
    # 4. Preparar resposta final
    final_response = {
        "data_for_dashboard": calculation_results,
        "narrative_report": text_report,
    }

    # Guarda os dados do relatório na sessão para a próxima página
    session['report_data'] = final_response
    session.pop('conversation_history', None) # Limpa o histórico da conversa
    
    return jsonify({"status": "success", "redirect_url": url_for('main.show_report')})


@routes.route("/report")
def show_report():
    report_data = session.get('report_data', None)
    if not report_data:
        return redirect(url_for('main.home'))
    return render_template("calculator.html", report_data=report_data)


# --- Rotas da Calculadora Direta ---

@routes.route('/calculator')
def show_calculator_form():
    return render_template('direct_calculator.html')


@routes.route('/calculator', methods=['POST'])
def handle_calculator_form():
    # 1. Extrair dados do formulário
    sanitized_data = {
        'km_carro': request.form.get('km_carro', type=float),
        'tipo_combustivel': request.form.get('tipo_combustivel') or None,
        'km_onibus': request.form.get('km_onibus', type=float),
        'kwh_eletricidade': request.form.get('kwh_eletricidade', type=float),
        'kg_gas_glp': (request.form.get('botijoes_gas', type=float) or 0) * 13.0
    }

    # 2. Calcular pegada (reutilizando o serviço)
    calculation_results = carbon_calculator.calculate_footprint(sanitized_data)

    # 3. Gerar relatório (reutilizando o serviço)
    text_report = chatbot_service.generate_narrative_report(calculation_results)
    
    # 4. Preparar resposta final
    final_response = {
        "data_for_dashboard": calculation_results,
        "narrative_report": text_report,
    }

    session['report_data'] = final_response
    return redirect(url_for('main.show_report'))