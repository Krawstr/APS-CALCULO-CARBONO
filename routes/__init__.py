"""
Inicialização do pacote routes
"""
from flask import Blueprint

# Criar blueprint principal UMA VEZ aqui
routes = Blueprint('main', __name__)

from routes import auth_routes, chat_routes, report_routes, profile_routes
