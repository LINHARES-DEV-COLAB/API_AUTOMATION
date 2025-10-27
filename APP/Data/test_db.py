import os
import sqlite3

def test_network_database():
    network_path = r"\\fileserver\tic\Desenvolvedores\_db"
    db_path = os.path.join(network_path, "automation_api.db")
    
    print(f"🔍 Testando acesso à rede: {network_path}")
    
    # Testa se o caminho é acessível
    if not os.path.exists(network_path):
        print("❌ Caminho de rede não acessível!")
        return False
    
    print("✅ Caminho de rede acessível")
    
    # Testa escrita no diretório
    test_file = os.path.join(network_path, "test_write.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Permissão de escrita OK")
    except Exception as e:
        print(f"❌ Sem permissão de escrita: {e}")
        return False
    
    # Testa conexão com o banco
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Testa leitura
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Conexão com banco OK - {len(tables)} tabelas encontradas")
        
        for table in tables:
            print(f"   - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao conectar com banco: {e}")
        return False

if __name__ == "__main__":
    test_network_database()