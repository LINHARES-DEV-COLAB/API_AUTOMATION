# debug_env.py
import os
from dotenv import load_dotenv

print("🔍 Diagnóstico de Variáveis de Ambiente:")
print("=" * 50)

# Carrega o .env
load_dotenv()

# Verifica se o .env está sendo carregado
env_file = '.env'
if os.path.exists(env_file):
    print(f"✅ Arquivo .env encontrado: {os.path.abspath(env_file)}")
    
    with open(env_file, 'r') as f:
        content = f.read()
        # Oculta a senha
        safe_content = content
        if 'SUPABASE_DB_URL' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'SUPABASE_DB_URL' in line and '://' in line:
                    parts = line.split('@', 1)
                    if len(parts) > 1:
                        user_pass = parts[0].split(':')
                        if len(user_pass) >= 3:
                            user_pass[2] = '***'
                            lines[i] = ':'.join(user_pass) + '@' + parts[1]
            safe_content = '\n'.join(lines)
        
        print("Conteúdo do .env (senha oculta):")
        print(safe_content)
else:
    print(f"❌ Arquivo .env NÃO encontrado em: {os.path.abspath('.')}")

print("\n📋 Variáveis de ambiente carregadas:")
supabase_url = os.getenv("SUPABASE_DB_URL")
if supabase_url:
    print(f"✅ SUPABASE_DB_URL: {supabase_url.split('@')[0].split(':')[0]}:***@{supabase_url.split('@')[1]}")
else:
    print("❌ SUPABASE_DB_URL: NÃO DEFINIDA")

print(f"📁 Diretório atual: {os.getcwd()}")