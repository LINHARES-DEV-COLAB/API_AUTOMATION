# seed_db.py
import os
from APP.extensions import db
from APP.Models.models import Sector, Automation  # ajuste se tiver outras tabelas
from main import app
from pathlib import Path
import sys  

def run_seed():
    with app.app_context():
        db.create_all()
    # idempotente: só cria se não existir
    if Sector.query.count() == 0:
        s1 = Sector(name="Financeiro")
        s2 = Sector(name="Vendas")
        db.session.add_all([s1, s2])
        db.session.flush()  # garante IDs para relacionar

        a1 = Automation(
            name="Conciliação Honda",
            description="Valida lotes e concilia extratos do Banco Honda.",
            sector_id=s1.id,
        )
        a2 = Automation(
            name="Relatório de Títulos",
            description="Gera relatório consolidado de títulos a receber.",
            sector_id=s1.id,
        )
        a3 = Automation(
            name="Importação de Leads",
            description="Importa leads e distribui para vendedores.",
            sector_id=s2.id,
        )
        db.session.add_all([a1, a2, a3])

        db.session.commit()
        print("👉 Seed: setores e automações criados.")
    else:
        print("👉 Seed: já existem setores; nada a fazer.")

if __name__ == "__main__":
    with app.app_context():
        # cria tabelas se não existirem
        db.create_all()
        print("DB URL:", app.config["SQLALCHEMY_DATABASE_URI"])
        print("instance_path:", app.instance_path)
        run_seed()
        print(f"✅ Seed concluído em: {os.path.join(app.instance_path, 'catalog.db')}")
