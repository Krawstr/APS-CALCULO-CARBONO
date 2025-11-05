"""
Utilitários para extração de dados
"""
import json
import re
import google.generativeai as genai


def extract_data_from_conversation(conversation_history, max_retries=3):
    """Extrai dados da conversa com retry"""
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 Tentativa {attempt} - Extraindo...")
            
            prompt = f"""
            Analise e extraia os dados: {json.dumps(conversation_history, ensure_ascii=False)}
            
            Retorne APENAS JSON válido:
            {{
                "km_carro": número ou null,
                "tipo_combustivel": "gasolina"|"etanol"|"diesel"|null,
                "km_onibus": número ou null,
                "kwh_eletricidade": número ou null,
                "kg_gas_glp": número ou null
            }}
            
            Regras:
            - "1 botijão" = 13
            - "2 botijões" = 26
            - Extraia apenas números
            """
            
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(prompt).text
            
            # Limpar resposta
            clean = response.strip()
            if clean.startswith('```'):
                clean = re.sub(r'```(?:json)?\s*', '', clean).strip('`').strip()
            
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                print(f"✅ Dados extraídos: {data}")
                return sanitize_data(data)
            
        except Exception as e:
            print(f"❌ Falha {attempt}: {e}")
            if attempt == max_retries:
                return extract_manually(conversation_history)
    
    return None


def sanitize_data(extracted_data):
    """Sanitiza e valida dados extraídos"""
    sanitized = {}
    
    for key, value in extracted_data.items():
        if value is None:
            sanitized[key] = None
            continue
        
        if key == 'tipo_combustivel':
            sanitized[key] = str(value).lower() if value else None
        else:
            try:
                numeric = re.sub(r'[^\d.]', '', str(value))
                if numeric:
                    num = float(numeric)
                    if key == 'kg_gas_glp' and num <= 5:
                        sanitized[key] = num * 13.0
                    else:
                        sanitized[key] = num
                else:
                    sanitized[key] = None
            except:
                sanitized[key] = None
    
    return sanitized


def extract_manually(conversation_history):
    """Extração manual como fallback"""
    data = {
        'km_carro': None,
        'tipo_combustivel': None,
        'km_onibus': None,
        'kwh_eletricidade': None,
        'kg_gas_glp': None
    }
    
    try:
        text = ' '.join([msg['parts'][0] for msg in conversation_history if msg['role'] == 'user'])
        text_lower = text.lower()
        
        # Detectar carro
        if 'não' in text_lower and 'carro' in text_lower:
            data['km_carro'] = None
            data['tipo_combustivel'] = None
        else:
            km_match = re.search(r'(\d+)\s*km', text, re.IGNORECASE)
            if km_match:
                data['km_carro'] = float(km_match.group(1))
            
            if 'gasolina' in text_lower:
                data['tipo_combustivel'] = 'gasolina'
            elif 'etanol' in text_lower:
                data['tipo_combustivel'] = 'etanol'
            elif 'diesel' in text_lower:
                data['tipo_combustivel'] = 'diesel'
        
        # kWh
        kwh_match = re.search(r'(\d+)\s*kwh', text, re.IGNORECASE)
        if kwh_match:
            data['kwh_eletricidade'] = float(kwh_match.group(1))
        
        # Botijões
        botijao_match = re.search(r'(\d+)\s*botij', text, re.IGNORECASE)
        if botijao_match:
            data['kg_gas_glp'] = float(botijao_match.group(1)) * 13.0
        
        print(f"📋 Extração manual: {data}")
        return data
        
    except Exception as e:
        print(f"❌ Erro extração manual: {e}")
        return None
