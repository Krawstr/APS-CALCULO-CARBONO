from src.extensions import db
from src.models import ChatHistory
import json


def save_chat_to_history(user_id, history_log, extracted_data, results, narrative):
    """
    Salva uma conversa completa e o seu relatório na base de dados.
    ATUALIZADO: Agora usa user_id ao invés de session_key
    
    Args:
        user_id (int): O ID do usuário autenticado
        history_log (list): O log da conversa (lista de dicts)
        extracted_data (dict): Os dados extraídos pela IA
        results (dict): Os resultados do cálculo (dados do dashboard)
        narrative (str): O relatório em texto
        
    Returns:
        tuple: (success: bool, message: str|None)
    """
    try:
        # Cria a nova entrada no histórico
        new_chat = ChatHistory(
            user_id=user_id,
            conversation_log=json.dumps(history_log, ensure_ascii=False) if history_log else None,
            extracted_data=json.dumps(extracted_data, ensure_ascii=False),
            report_results=json.dumps(results, ensure_ascii=False),
            report_narrative=narrative
        )
        
        # Adiciona à sessão da base de dados e "commita"
        db.session.add(new_chat)
        db.session.commit()
        
        print(f"✅ Histórico salvo para usuário ID: {user_id}")
        return True, None
        
    except Exception as e:
        # Se algo der errado, faz rollback para não corromper a db
        db.session.rollback()
        print(f"❌ Erro ao salvar histórico: {e}")
        return False, str(e)


def get_user_history(user_id, limit=10):
    """
    Recupera o histórico de conversas de um usuário.
    
    Args:
        user_id (int): ID do usuário
        limit (int): Número máximo de registros a retornar
        
    Returns:
        list: Lista de objetos ChatHistory
    """
    try:
        history = ChatHistory.query.filter_by(user_id=user_id)\
            .order_by(ChatHistory.created_at.desc())\
            .limit(limit)\
            .all()
        return history
    except Exception as e:
        print(f"❌ Erro ao buscar histórico: {e}")
        return []


def get_chat_by_id(chat_id, user_id):
    """
    Recupera uma conversa específica (validando que pertence ao usuário).
    
    Args:
        chat_id (int): ID do chat
        user_id (int): ID do usuário (para validação)
        
    Returns:
        ChatHistory|None: Objeto ChatHistory ou None
    """
    try:
        chat = ChatHistory.query.filter_by(id=chat_id, user_id=user_id).first()
        return chat
    except Exception as e:
        print(f"❌ Erro ao buscar chat: {e}")
        return None


def delete_chat(chat_id, user_id):
    """
    Deleta uma conversa do histórico (validando que pertence ao usuário).
    
    Args:
        chat_id (int): ID do chat
        user_id (int): ID do usuário (para validação)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        chat = ChatHistory.query.filter_by(id=chat_id, user_id=user_id).first()
        if not chat:
            return False, "Conversa não encontrada ou não pertence a você."
        
        db.session.delete(chat)
        db.session.commit()
        
        print(f"🗑️ Chat {chat_id} deletado com sucesso.")
        return True, "Conversa deletada com sucesso."
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao deletar chat: {e}")
        return False, str(e)
