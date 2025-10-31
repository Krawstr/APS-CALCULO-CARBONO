# src/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    profile_picture = db.Column(db.String(200), default='default_avatar.png')  # NOVO
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reports = db.relationship('Report', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Dados do cálculo
    km_carro = db.Column(db.Float, nullable=True)
    tipo_combustivel = db.Column(db.String(20), nullable=True)
    km_onibus = db.Column(db.Float, nullable=True)
    kwh_eletricidade = db.Column(db.Float, nullable=True)
    kg_gas_glp = db.Column(db.Float, nullable=True)
    
    # Resultados
    total_kg_co2e = db.Column(db.Float, nullable=False)
    transporte_kg_co2e = db.Column(db.Float, default=0.0)
    energia_eletrica_kg_co2e = db.Column(db.Float, default=0.0)
    gas_cozinha_kg_co2e = db.Column(db.Float, default=0.0)
    
    # Relatório narrativo gerado pela IA
    narrative_report = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        """Converte o relatório para dicionário"""
        return {
            'id': self.id,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'data_for_dashboard': {
                'details_kg_co2e': {
                    'transporte': self.transporte_kg_co2e,
                    'energia_eletrica': self.energia_eletrica_kg_co2e,
                    'gas_cozinha': self.gas_cozinha_kg_co2e
                },
                'total_kg_co2e': self.total_kg_co2e
            },
            'input_data': {
                'km_carro': self.km_carro,
                'tipo_combustivel': self.tipo_combustivel,
                'km_onibus': self.km_onibus,
                'kwh_eletricidade': self.kwh_eletricidade,
                'kg_gas_glp': self.kg_gas_glp
            },
            'narrative_report': self.narrative_report
        }
    
    def __repr__(self):
        return f'<Report {self.id} - {self.total_kg_co2e} kg CO2e>'
