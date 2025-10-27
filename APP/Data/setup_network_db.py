# setup_network_db_complete.py
import os
import sqlite3

def setup_complete_database():
    # Caminho da rede
    network_path = r"T:\Desenvolvedores\_db"
    db_path = os.path.join(network_path, "automation_api.db")
    
    print(f"🔧 Configurando banco completo em: {db_path}")
    
    # Garante que o diretório existe
    os.makedirs(network_path, exist_ok=True)
    
    try:
        # Conecta ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # =============================================
        # CRIAÇÃO DAS TABELAS
        # =============================================
        
        # Tabela store
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS store (
                id TEXT PRIMARY KEY,
                cnpj TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela departments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                code TEXT UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_superuser BOOLEAN DEFAULT 0,
                department_id TEXT REFERENCES departments(id),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela automations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                script_path TEXT NOT NULL,
                type TEXT CHECK(type IN ('manual', 'scheduled', 'triggered')) NOT NULL,
                schedule_cron TEXT,
                is_active BOOLEAN DEFAULT 1,
                max_execution_time INTEGER DEFAULT 3600,
                created_by TEXT REFERENCES users(id),
                department_id TEXT REFERENCES departments(id),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela executions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                automation_id TEXT REFERENCES automations(id),
                triggered_by TEXT REFERENCES users(id),
                status TEXT CHECK(status IN ('pending', 'running', 'success', 'failed', 'cancelled')) DEFAULT 'pending',
                start_time DATETIME,
                end_time DATETIME,
                exit_code INTEGER,
                output_log TEXT,
                error_log TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela automation_configs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_configs (
                id TEXT PRIMARY KEY,
                automation_id TEXT REFERENCES automations(id),
                config_key TEXT NOT NULL,
                config_value TEXT,
                config_type TEXT CHECK(config_type IN ('string', 'number', 'boolean', 'json')) DEFAULT 'string',
                is_secret BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # =============================================
        # ÍNDICES
        # =============================================
        
        # Departments
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_departments_active ON departments(is_active)')
        
        # Users
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_department ON users(department_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)')
        
        # Automations
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_automations_department ON automations(department_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_automations_type ON automations(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_automations_active ON automations(is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_automations_created_by ON automations(created_by)')
        
        # Executions
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_executions_automation ON executions(automation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_executions_triggered_by ON executions(triggered_by)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_executions_created_at ON executions(created_at)')
        
        # Automation_configs
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_configs_automation ON automation_configs(automation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_configs_key ON automation_configs(config_key)')
        
        # =============================================
        # DADOS INICIAIS
        # =============================================
        
        print("📝 Inserindo dados iniciais...")
        
        # Departments
        cursor.execute('''
            INSERT OR IGNORE INTO departments (id, name, description, code, is_active)
            VALUES
                ('dep_ti',  'Tecnologia da Informação', 'Responsável por infraestrutura, desenvolvimento e suporte técnico', 'TI',  1),
                ('dep_fin', 'Financeiro',               'Gestão financeira, contabilidade e orçamento',                    'FIN', 1)
        ''')
        
        # Users
        password_hash = '$2b$12$STTJ75kKPspPqT8TqQwhWOTcd60/yYF5Daa0D6SLKoC7T9mL6ZiGm'
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (id, email, username, hashed_password, is_active, is_superuser, department_id)
            VALUES
                ('lucas.lima',      'sousa.lima@grupolinhares.com.br',     'sousa.lima',      ?, 1, 1, 'dep_ti'),
                ('wellington.lima', 'wellington.lima@grupolinhares.com.br','wellington.lima', ?, 1, 1, 'dep_ti'),
                ('dev.linhares',    'dev.linhares@grupolinhares.com.br',   'dev.linhares',    ?, 1, 1, 'dep_ti')
        ''', (password_hash, password_hash, password_hash))
        
        # Stores
        stores_data = [
            ('TIANGUA',             '07.256.867/0016-38', 'ARES - MOTOS - TIANGUA',         'FINANCER',  '$2b$12$6vlDU/AqF/GhPzTFWRhkmeJzJo1v88IBy1YPJ77EN6u/9k1tARwAy', 1),
            ('IPU',                 '07.256.867/0013-95', 'ARES - MOTOS - IPU',             'FINANCEIRO','$2b$12$jBTfEDgaegM8FMn1RA68OuQ81Dx8wmZrOpwCANXE4jBeRiwqgmuGm', 1),
            ('TERRA_SANTA_INHAMUNS','N/A-TERRA_SANTA_INHAMUNS', 'TERRA SANTA (INHAMUNS)',   'FINANCEI22','$2b$12$dulIfUC4FGy5ozSK82SNU.fMItd76PBVQMzpdo6TPzKl3q9YWsv02', 1),
            ('ARES_IGUATU',         '07.256.867/0017-19', 'ARES - MOTOS - IGUATU',         'FINANCEI',  '$2b$12$RMwrkZqr4wAUB11GZ.6O7etp6sIDOkfHjwAb/QkcxbCwPzcMUgQ5W', 1),
            ('ICO',                 '07.256.867/0015-57', 'ARES - MOTOS - ICO',             'FINANCE',   '$2b$12$XzKbUUtLi.XYCGlt1Sr1vObf7MOg9e7tEK8VrSwP0oszOyGWkuvvy', 1),
            ('JUAZEIRO',            '07.256.867/0001-51', 'ARES - MOTOS - JUAZEIRO',        'FINANCEIRO','$2b$12$K4ufCxNrYn2T3Ry2uP9uIeHo8Nz.B6LU6PBV88DZoRvzCUFIw3qgi', 1),
            ('CAMPOS_SALES',        '07.256.867/0003-13', 'ARES - MOTOS - CAMPO SALES',     'FINANCE',   '$2b$12$JNjuX7LuxPdavLvgBcTB8ucFkFn5SOkCQkFJeZz8jUbm43hs5dODe', 1),
            ('CRATO',               '07.256.867/0002-32', 'ARES - MOTOS - CRATO',           'FINANCEIRO','$2b$12$HPcGzDAzA928YOvKBsbJz.sgKMNAbTUHlEXUz.20FZmQAYy8PHlcS', 1),
            ('BREJO_SANTO',         '07.256.867/0004-02', 'ARES - MOTOS - BREJO SANTO',     'FINANCE',   '$2b$12$XrjG3XU3ILsb3.4K2Dccu.jHC1mwCbUQGbelniqJ2pDoTwDVxmYA6', 1),
            ('ITAPAJE',             '07.256.867/0009-09', 'ARES - MOTOS - ITAPAJÉ',         'FINANCER',  '$2b$12$pFKfOcn7vxqMgiLJz9E0E.P/YTuZSItCx/LjJgnjCggi6GYR7f4v.', 1),
            ('ITAPIPOCA',           '07.256.867/0007-47', 'ARES - MOTOS - ITAPIPOCA',       'FINANCER',  '$2b$12$KsxTqxYMiHRWEcxwf002vO1oWOjcmfWA4UfxMbYWyTyBj.l0c3sD2', 1),
            ('ACM',                 '07.256.867/0024-48', 'ARES MOTOS - ACM',               'FINANCEIRO','$2b$12$dG5.CdCWsL7mmGKO3hHze.1UHH5xg1JE6glbXNf8zMnZ24cul5jcK', 1),
            ('CALCADA',             '07.256.867/0025-29', 'ARES MOTOS - CALÇADA',           'FINANCEIRO','$2b$12$GcFNXPUNOaVBVFTlrfuMSOlTrWUUsKEpRLsUsJVNMZkl65dGYGn0a', 1),
            ('LITORAL',             '07.256.867/0026-00', 'ARES MOTOS - LITORAL',           'FINANCEIRO','$2b$12$X0kKcnRmw0ph6N1YRzd1iuPYrl8Htmk7XJi/zpE5EYKvlJJTFCKfC', 1),
            ('BONOCO',              'N/A-BONOCO',         'ARES MOTOS - BONOCÔ',            'FINANCEIRO','$2b$12$gqEPicAdLMK3orxLuZTMwu2TR15XU4lGuHswxa6c9uOqaoIAD0HhO', 1),
            ('VALENCA',             '07.256.867/0029-52', 'ARES MOTOS - VALENÇA',           'FINANCEIRO','$2b$12$e/9/6uST4ll6k51lgxgeVedb70Z.iJUsF.i9R8yGc402EmPhI7Akq', 1),
            ('CRUZ_DAS_ALMAS',      '07.256.867/0030-96', 'ARES MOTOS - CRUZ DAS ALMAS',    'FINANCEIRO','$2b$12$zveH7I.FRNd4v4Vl4qqHhuaVcxo0wazFeM7h7UZcbSvlOhfE4QfsC', 1),
            ('NOVA_ONDA_ARACATI',   '07.203.485/0001-60', 'NOVA ONDA - MOTOS - ARACATI',    'FINACEIROA','$2b$12$vdhkkp20qERKl53AYsBA3uubJkiDHZZb8gkku87KQg9fcMaFCHvcm', 1),
            ('NOVA_ONDA_LIMOEIRO',  '07.203.485/0002-40', 'NOVA ONDA - MOTOS - LIMOEIRO',   'FINANCE',   '$2b$12$vxsNTOUZO6CDUJFTmekNx.N7YH5o5Cckr7hj1F8GCofQ3/PVfUm5e', 1),
            ('NOVA_ONDA_IGUATU',    '07.203.485/0003-21', 'NOVA ONDA - MOTOS - IGUATU',     'FINANCEIRO','$2b$12$u5E9OUf3D5JXnwkgcRBIuetY7NwS1k8w5pMtHkz/B4DuCj3m/lgga', 1)
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO store (id, cnpj, name, username, password_hash, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', stores_data)
        
        # Automations
        automations_data = [
            ('solicitacao_carga',         'Solicitação de carga',        'descrição genérica', 'APP/Controllers/solicitacao_carga_controller.py',       'manual', 1, 'dep_fin', 'wellington.lima'),
            ('baixas_pan',                'Baixas PAN',                  'descrição genérica', 'APP/Controllers/pan_controller.py',                     'manual', 1, 'dep_fin', 'lucas.lima'),
            ('conciliacao_cdc_honda',     'Conciliação CDC Honda',       'descrição genérica', 'APP/Controllers/conciliacao_cdc_honda_controller.py',   'manual', 1, 'dep_fin', 'wellington.lima'),
            ('baixas_cnh_honda',          'Baixas CNH Honda',            'descrição genérica', 'APP/Controllers/baixa_arquivos_cnh_honda_controller.py','manual', 1, 'dep_fin', 'wellington.lima'),
            ('preparacao_baixas',         'Preparação Baixas',           'descrição genérica', 'APP/Controllers/preparacao_baixas_controller.py',       'manual', 1, 'dep_fin', 'wellington.lima'),
            ('fidc',                      'FIDC',                        'descrição genérica', 'APP/Controllers/fidc_controller.py',                    'manual', 1, 'dep_fin', 'lucas.lima')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO automations (id, name, description, script_path, type, is_active, department_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', automations_data)
        
        # =============================================
        # TRIGGERS
        # =============================================
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_departments_updated_at 
                AFTER UPDATE ON departments
            BEGIN
                UPDATE departments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_users_updated_at 
                AFTER UPDATE ON users
            BEGIN
                UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS update_automations_updated_at 
                AFTER UPDATE ON automations
            BEGIN
                UPDATE automations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
        ''')
        
        conn.commit()
        
        # =========================
        # CONFERÊNCIA
        # =========================
        print("\n📊 CONFERÊNCIA DOS DADOS INSERIDOS:")
        
        cursor.execute("SELECT COUNT(*) FROM departments")
        dept_count = cursor.fetchone()[0]
        print(f"   Departamentos: {dept_count}")
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"   Usuários: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM store")
        store_count = cursor.fetchone()[0]
        print(f"   Lojas: {store_count}")
        
        cursor.execute("SELECT COUNT(*) FROM automations")
        auto_count = cursor.fetchone()[0]
        print(f"   Automações: {auto_count}")
        
        print(f"\n✅ Banco configurado com sucesso!")
        print(f"📁 Local: {db_path}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao configurar banco: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    setup_complete_database()