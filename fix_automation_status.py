# fix_automation_status.py
import sqlite3
import os

def check_and_fix_automation():
    db_path = r"T:\Desenvolvedores\_db\automation_api.db"
    
    print(f"📁 Verificando banco: {db_path}")
    print(f"📁 Existe?: {os.path.exists(db_path)}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Verifica TODAS as automações
    cursor.execute("SELECT id, name, is_active FROM automations")
    all_automations = cursor.fetchall()
    
    print("\n🔍 TODAS AS AUTOMAÇÕES NO BANCO:")
    for auto in all_automations:
        id, name, is_active = auto
        print(f"   {id:20} | {name:30} | is_active: {is_active}")
    
    # 2. Verifica específico da FIDC
    cursor.execute("SELECT id, name, is_active FROM automations WHERE id = 'fidc'")
    fidc_automation = cursor.fetchone()
    
    print(f"\n🎯 AUTOMAÇÃO FIDC ESPECÍFICA:")
    if fidc_automation:
        id, name, is_active = fidc_automation
        print(f"   ID: {id}")
        print(f"   Name: {name}")
        print(f"   is_active: {is_active}")
        
        # 3. Se estiver como 1, muda para 0
        if is_active == 1:
            print(f"\n🔄 MUDANDO is_active de 1 para 0...")
            cursor.execute("UPDATE automations SET is_active = 0 WHERE id = 'fidc'")
            conn.commit()
            print(f"✅ UPDATE executado!")
            
            # Verifica novamente
            cursor.execute("SELECT is_active FROM automations WHERE id = 'fidc'")
            new_value = cursor.fetchone()[0]
            print(f"✅ Novo valor: {new_value}")
        else:
            print(f"✅ Já está como {is_active}")
    else:
        print("❌ Automação 'fidc' não encontrada")
    
    conn.close()
    print("🔒 Conexão fechada")

if __name__ == "__main__":
    check_and_fix_automation()