"""
Microsserviço de Chat/Conversação
Responsável por: chatbot, conversas com IA
"""
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
import google.generativeai as genai
from routes import routes
from routes.utils.ai_helper import generate_ai_response, SYSTEM_PROMPT

# Histórico global de conversas
conversation_history = []


@routes.route("/")
@login_required
def home():
    """Página inicial do chat"""
    return render_template("index.html", username=current_user.username)


@routes.route("/start_conversation", methods=['POST'])
@login_required 
def start_conversation():
    """Inicia uma nova conversa com a IA"""
    global conversation_history
    
    conversation_history = [
        {'role': 'user', 'parts': [SYSTEM_PROMPT]},
        {'role': 'model', 'parts': [
            "Oi! Tudo bem? Eu sou a Dalva Carlinhos 🌱\n\n"
            "Vou te ajudar a calcular sua pegada de carbono mensal. "
            "É bem rapidinho e depois te dou dicas personalizadas pra reduzir suas emissões!\n\n"
            "Vamos lá... você tem carro?"
        ]}
    ]
    
    return jsonify({"response": conversation_history[-1]['parts'][0]})


@routes.route("/send_message", methods=['POST'])
@login_required  
def send_message():
    """Envia mensagem e recebe resposta da IA"""
    global conversation_history
    
    message = request.get_json()
    if not message or 'text' not in message:
        return jsonify({"error": "Mensagem inválida"}), 400

    user_text = message['text']
    conversation_history.append({'role': 'user', 'parts': [user_text]})

    # Gerar resposta com retry automático
    response_text = generate_ai_response(conversation_history)
    
    if response_text:
        conversation_history.append({'role': 'model', 'parts': [response_text]})
        return jsonify({"response": response_text})
    else:
        return jsonify({"error": "Erro ao gerar resposta"}), 500


@routes.route('/saiba-mais')
def learn_more():
    """Página educativa sobre pegada de carbono"""
    return render_template('learn_more.html')
