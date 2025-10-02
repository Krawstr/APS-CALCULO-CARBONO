import os
import json
import re 
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import carbon_calculator

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = Flask(__name__)
CORS(app)

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

@app.route("/start_conversation", methods=['POST'])
def start_conversation():
    global conversation_history
    conversation_history = [
        {'role': 'user', 'parts': [SYSTEM_PROMPT]},
        {'role': 'model', 'parts': ["Olá! Eu sou Dalva Carlinhos, sua assistente para cálculo de pegada de carbono. Você possui carro?"]}
    ]
    return jsonify({"response": conversation_history[-1]['parts'][0]})

@app.route("/send_message", methods=['POST'])
def send_message():
    global conversation_history
    message = request.get_json()
    if not message or 'text' not in message:
        return jsonify({"error": "Mensagem inválida"}), 400

    user_text = message['text']
    conversation_history.append({'role': 'user', 'parts': [user_text]})

    model = genai.GenerativeModel('gemini-2.0-flash')
    chat = model.start_chat(history=conversation_history)
    response = chat.send_message(user_text)
    assistant_response = response.text
    
    conversation_history.append({'role': 'model', 'parts': [assistant_response]})
    return jsonify({"response": assistant_response})

@app.route("/generate_report", methods=['POST'])
def generate_report():
    global conversation_history

    extraction_prompt = f"""
    Analise a seguinte conversa e extraia os dados para o cálculo da pegada de carbono. A conversa é: {json.dumps(conversation_history)}
    Sua resposta DEVE SER APENAS um objeto JSON, sem nenhum texto adicional. Use as seguintes chaves: "km_carro", "tipo_combustivel", "km_onibus", "kwh_eletricidade", "kg_gas_glp".
    Para "tipo_combustivel", use um dos seguintes valores: "gasolina", "etanol", "diesel". Se uma informação não foi fornecida, use o valor null.
    Para valores numéricos, extraia APENAS o número (ex: "1 botijao" -> 13, "600km" -> 600).
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response_json_str = model.generate_content(extraction_prompt).text
    
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
        print(f"Resposta recebida da IA: {response_json_str}")
        return jsonify({"error": "Não foi possível extrair os dados da conversa."}), 500

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

    text_report = model.generate_content(report_prompt).text
    
    final_response = {
        "data_for_dashboard": calculation_results,
        "narrative_report": text_report,
    }
    
    return jsonify(final_response)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)