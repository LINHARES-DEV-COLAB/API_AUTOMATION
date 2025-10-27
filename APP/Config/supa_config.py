# # APP/Config/supa_config.py
# import os
# from flask_sqlalchemy import SQLAlchemy

# db = SQLAlchemy()

# def init_db(app):
#     uri = os.getenv("SUPABASE_DB_URL", "").strip()
#     if not uri:
#         raise RuntimeError("SUPABASE_DB_URL não configurada")

#     # Garante SSL e força IPv4 se necessário
#     if "sslmode=" not in uri:
#         sep = "&" if "?" in uri else "?"
#         uri = f"{uri}{sep}sslmode=require"
    
#     # Adiciona timeout e opções para IPv4
#     if "connect_timeout=" not in uri:
#         sep = "&" if "?" in uri else "?"
#         uri = f"{uri}{sep}connect_timeout=10"

#     app.config["SQLALCHEMY_DATABASE_URI"] = uri
#     app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#     app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
#         "pool_pre_ping": True,
#         "pool_recycle": 300,
#         "connect_args": {
#             "sslmode": "require",
#             "connect_timeout": 10,
#             # Força tentativa IPv4 primeiro
#             "options": "-c address_type_preference=ipv4"
#         },
#     }

#     if not getattr(app, "extensions", None) or "sqlalchemy" not in app.extensions:
#         db.init_app(app)



# APP/Config/supa_config.py
import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    # Caminho da rede compartilhada
    network_path = r"\\fileserver\tic\Desenvolvedores\_db"
    db_filename = "automation_api.db"
    db_path = os.path.join(network_path, db_filename)
    
    # Garante que o diretório existe
    os.makedirs(network_path, exist_ok=True)
    
    # URI do SQLite
    uri = f"sqlite:///{db_path}"
    
    app.config["SQLALCHEMY_DATABASE_URI"] = uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    print(f"📁 Banco SQLite: {db_path}")
    
    # Evita registrar 2x
    if not getattr(app, "extensions", None) or "sqlalchemy" not in app.extensions:
        db.init_app(app)