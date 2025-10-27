# test_final.py
import os
import psycopg2
from dotenv import load_dotenv

print("🚀 Teste Final de Conexão")
print("=" * 40)

load_dotenv()

# Pega a URL corretamente
supabase_url = os.getenv("SUPABASE_DB_URL")

if not supabase_url:
    print("❌ SUPABASE_DB_URL não encontrada!")
    exit(1)

print("🔗 String de conexão carregada:")
# Remove aspas se existirem
supabase_url = supabase_url.strip('"')

# Mostra de forma segura
if "@" in supabase_url:
    user_part, host_part = supabase_url.split("@", 1)
    safe_display = user_part.split(":")[0] + ":***@" + host_part
    print(f"   {safe_display}")

print("\n🔄 Tentando conectar...")

try:
    conn = psycopg2.connect(supabase_url)
    print("✅ CONEXÃO BEM-SUCEDIDA!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"📊 PostgreSQL: {version[0].split(',')[0]}")
    
    cursor.close()
    conn.close()
    print("🎉 Tudo funcionando!")
    
except psycopg2.OperationalError as e:
    print(f"❌ Erro de conexão: {e}")
    if "password authentication failed" in str(e):
        print("💡 Verifique a SENHA no Supabase Dashboard")
    elif "could not translate host name" in str(e):
        print("💡 Problema de DNS/rede - teste em hotspot")
        
except Exception as e:
    print(f"❌ Erro: {e}")