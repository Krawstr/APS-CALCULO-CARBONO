"""
Utilitários para IA (Gemini)
"""
import google.generativeai as genai
import json


SYSTEM_PROMPT = """
Você é a CAROL, uma assistente virtual brasileira, calorosa e especialista em sustentabilidade. 
Você conversa de forma natural, como uma amiga que quer ajudar.

Seu objetivo é coletar informações para calcular a pegada de carbono mensal do usuário, mas sem parecer um formulário. 
Seja empática, use emojis ocasionalmente, e adapte suas respostas ao tom do usuário.

Informações que você precisa coletar (faça de forma conversacional):
1. TRANSPORTE:
   - Tem carro? Se sim, qual combustível (gasolina, etanol ou diesel)?
   - Quantos km roda por mês aproximadamente?
   - Usa transporte público? Quantos km por mês?

2. ENERGIA EM CASA:
   - Consumo de eletricidade em kWh (está na conta de luz)
   - Quantos botijões de gás de 13kg usa por mês?

IMPORTANTE:
- Seja flexível na ordem das perguntas
- Se o usuário der várias informações de uma vez, agradeça e peça o que ainda falta
- Use linguagem casual e brasileira
- Quando tiver TODOS os dados, pergunte: "Perfeito! Tenho tudo que preciso. Quer que eu gere seu relatório agora? 😊"
- Se o usuário fizer perguntas sobre sustentabilidade, responda educadamente antes de continuar
"""


def generate_ai_response(conversation_history, max_retries=3):
    """Gera resposta da IA com retry automático"""
    for attempt in range(1, max_retries + 1):
        try:
            print(f"💬 Tentativa {attempt} - Gerando resposta...")
            
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(conversation_history)
            
            print(f"✅ Resposta gerada")
            return response.text
            
        except Exception as e:
            print(f"❌ Tentativa {attempt} falhou: {e}")
            if attempt == max_retries:
                return "Desculpa, tive um problema técnico. Pode repetir? 😅"
    
    return None


def generate_report_text(calculation_results, max_retries=2):
    """Gera texto narrativo do relatório"""
    report_prompt = f"""
    Você é a CAROL. Crie um relatório COMPLETO e BEM FORMATADO sobre pegada de carbono.

    Dados (kg CO2e/mês): {json.dumps(calculation_results, ensure_ascii=False, indent=2)}

    ESTRUTURA EXATA (copie essa estrutura):

    ## Seu Relatório de Pegada de Carbono 🌱

    Olá! Aqui está sua análise completa de emissões. Vamos construir um futuro mais verde juntos! 💚

    ### Resultado Total

    Total mensal: {calculation_results['total_kg_co2e']:.2f} kg CO2e/mês = {calculation_results['total_kg_co2e'] * 12:.2f} kg CO2e/ano

    ### Análise por Categoria

    [Identifique a categoria de MAIOR impacto (transporte, energia ou gás) e explique em 2-3 frases]

    ### Dicas para Redução

    1. **[Nome da Dica]**: [Descrição prática e específica em 1-2 linhas]

    2. **[Nome da Dica]**: [Descrição prática e específica em 1-2 linhas]

    3. **[Nome da Dica]**: [Descrição prática e específica em 1-2 linhas]

    ### Como Compensar sua Pegada 💚

    Compensar sua pegada é investir no planeta! Apoie projetos de reflorestamento e ajude a neutralizar suas emissões.

    **Créditos Necessários:**
    - Mensal: {calculation_results['total_kg_co2e']:.2f} kg CO2e
    - Anual: {calculation_results['total_kg_co2e'] * 12:.2f} kg CO2e
    - Árvores: {int(calculation_results['total_kg_co2e'] * 12 / 22)} por ano

    **Organizações:**

    1. SOS Mata Atlântica (R$ 30-50/ton)
    2. Iniciativa Verde (R$ 40-60/ton)
    3. Moss.Earth (R$ 50-80/ton)

    **Custo estimado:**
    - Mensal: R$ {(calculation_results['total_kg_co2e'] / 1000) * 40:.2f} a R$ {(calculation_results['total_kg_co2e'] / 1000) * 60:.2f}
    - Anual: R$ {(calculation_results['total_kg_co2e'] * 12 / 1000) * 40:.2f} a R$ {(calculation_results['total_kg_co2e'] * 12 / 1000) * 60:.2f}

    Cada ação conta! Escolha uma organização e plante um futuro mais verde hoje mesmo. 🌱

    REGRAS IMPORTANTES:
    - COPIE a estrutura EXATAMENTE como mostrada
    - Use ## para título principal e ### para subtítulos
    - Use **negrito** apenas nos nomes das dicas
    - Máximo 350 palavras
    - Tom brasileiro, amigável e motivador
    - Use APENAS esses emojis: 🌱 💚 🌳
    """
    
    for attempt in range(1, max_retries + 1):
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            text = model.generate_content(report_prompt).text.strip()
            print(f"✅ Relatório gerado ({len(text)} caracteres)")
            return text
        except Exception as e:
            print(f"❌ Falha ao gerar relatório: {e}")
            if attempt == max_retries:
                return generate_simple_report(calculation_results)
    
    return "Relatório gerado!"



def generate_simple_report(calculation_results):
    """Relatório fallback simples"""
    total = calculation_results['total_kg_co2e']
    details = calculation_results['details_kg_co2e']
    max_cat = max(details.items(), key=lambda x: x[1])
    
    names = {
        'transporte': 'Transporte',
        'energia_eletrica': 'Energia Elétrica',
        'gas_cozinha': 'Gás de Cozinha'
    }
    
    return f"""## Seu Relatório de Pegada de Carbono 🌱

Sua pegada mensal: **{total:.2f} kg CO2e**

Maior impacto: **{names[max_cat[0]]}** ({max_cat[1]:.2f} kg CO2e)

**Dicas:**
1. Reduza o consumo na categoria de maior impacto
2. Adote práticas sustentáveis
3. Compartilhe com amigos

Continue nessa jornada! 💚"""
