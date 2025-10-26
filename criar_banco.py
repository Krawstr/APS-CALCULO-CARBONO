from src import create_app
from src.extensions import db

print("🔄 Criando banco de dados...")

app = create_app()

with app.app_context():
    # Remove tabelas antigas (se existirem)
    db.drop_all()
    print("🗑️  Tabelas antigas removidas (se existiam)")
    
    # Cria todas as tabelas
    db.create_all()
    print("✅ Tabelas criadas com sucesso!")
    
    # Lista as tabelas criadas
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"📋 Tabelas no banco: {tables}")
