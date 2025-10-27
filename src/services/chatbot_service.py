# /src/services/chatbot_service.py

import google.generativeai as genai
import json
import re

# O Prompt do Sistema define o comportamento da Dalva
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

def initialize_chat():
    """
    Inicia uma nova conversa e retorna a primeira saudação.
    Retorna o histórico da conversa inicial.
    """
    history = [
        {'role': 'user', 'parts': [SYSTEM_PROMPT]},
        {'role': 'model', 'parts': ["Olá! Eu sou Dalva Carlinhos, sua assistente para cálculo de pegada de carbono. Você possui carro?"]}
    ]
    return history

def continue_chat(history, user_text):
    """
    Continua a conversa. Recebe o histórico e a nova mensagem do usuário.
    Retorna a resposta do modelo.
    """
    history.append({'role': 'user', 'parts': [user_text]})
    
    model = genai.GenerativeModel('gemini-2.0-flash') # Alterei para 1.5 flash, mais recente
    response = model.generate_content(history)
    assistant_response = response.text
    
    history.append({'role': 'model', 'parts': [assistant_response]})
    return assistant_response, history

def extract_data_from_chat(history):
    """
    Extrai dados estruturados (JSON) de um histórico de conversa.
    Retorna um dicionário com os dados sanitizados.
    """
    extraction_prompt = f"""
    Analise a seguinte conversa e extraia os dados para o cálculo da pegada de carbono. A conversa é: {json.dumps(history)}
    Sua resposta DEVE SER APENAS um objeto JSON, sem nenhum texto adicional. Use as seguintes chaves: "km_carro", "tipo_combustivel", "km_onibus", "kwh_eletricidade", "kg_gas_glp".
    Para "tipo_combustivel", use um dos seguintes valores: "gasolina", "etanol", "diesel". Se uma informação não foi fornecida, use o valor null.
    Para valores numéricos, extraia APENAS o número (ex: "1 botijao" -> 13, "600km" -> 600).
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response_json_str = model.generate_content(extraction_prompt).text
    
    # Limpeza e extração do JSON
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
        return None # Retorna None em caso de erro

    # Sanitização dos dados (muito importante!)
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
                
    return sanitized_data

def generate_narrative_report(calculation_results):
    """
    Usa a IA para gerar um relatório em texto amigável com base
    nos resultados do cálculo.
    """
    report_prompt = f"""
    Com base nos seguintes resultados do cálculo da pegada de carbono de um usuário (em kg de CO2e): {json.dumps(calculation_results)}
    Gere um relatório personalizado, amigável e otimista.
    - Comece com um resumo do resultado total.
    - Analise qual categoria foi a maior emissora.
    - Ofereça 3 dicas práticas e acionáveis para o usuário reduzir sua pegada, focando na categoria de maior impacto.
    - Termine com uma mensagem de encorajamento.
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    text_report = model.generate_content(report_prompt).text
    return text_report