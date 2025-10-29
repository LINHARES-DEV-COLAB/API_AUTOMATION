# test_fluxo_paginacao_corrigido.py
from Services.fidc_selenium_integration import SeleniumIntegration
from DTO.FIDC_DTO import LoginDTO
from Services.fidc_excel_integration import mapear_emps_para_nfs
from time import sleep
# test_fluxo_paginacao_corrigido.py
from Services.fidc_selenium_integration import SeleniumIntegration
from DTO.FIDC_DTO import LoginDTO
from Services.fidc_excel_integration import mapear_emps_para_nfs
from time import sleep

def fazer_pesquisa_com_autocomplete(bot):
    """Faz a pesquisa incluindo a seleção do autocomplete"""
    print("🔄 FAZENDO PESQUISA COM AUTOCOMPLETE...")
    
    resultado = bot.driver.execute_script("""
        const campoRevenda = document.querySelector('input[placeholder="Revenda"]');
        if (!campoRevenda) return {sucesso: false, motivo: 'Campo Revenda não encontrado'};
        
        campoRevenda.focus();
        campoRevenda.value = '';
        
        const texto = 'INHAMUNS';
        for (let i = 0; i < texto.length; i++) {
            campoRevenda.value = texto.substring(0, i + 1);
            campoRevenda.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        return {sucesso: true, etapa: 'texto_digitado'};
    """)
    
    if not resultado.get('sucesso'):
        return resultado
    
    print("✅ Texto 'INHAMUNS' digitado no campo Revenda")
    sleep(2)
    
    autocomplete_clicado = bot.driver.execute_script("""
        const opcoes = document.querySelectorAll('mat-option span');
        for (let opcao of opcoes) {
            if (opcao.textContent.includes('INHAMUNS MOTOS LTDA')) {
                opcao.click();
                return true;
            }
        }
        return false;
    """)
    
    if autocomplete_clicado:
        print("✅ Opção 'INHAMUNS MOTOS LTDA' selecionada")
        sleep(1)
    else:
        return {'sucesso': False, 'motivo': 'Autocomplete não encontrado'}
    
    pesquisar_clicado = bot.driver.execute_script("""
        const botoes = document.querySelectorAll('button');
        for (let botao of botoes) {
            if (botao.textContent.includes('Pesquisar') && !botao.disabled) {
                botao.click();
                return true;
            }
        }
        return false;
    """)
    
    if pesquisar_clicado:
        print("✅ Botão 'Pesquisar' clicado")
        sleep(3)
        return {'sucesso': True}
    else:
        return {'sucesso': False, 'motivo': 'Botão Pesquisar não encontrado'}

def verificar_proxima_pagina(bot):
    """Verifica se há próxima página - MESMA LÓGICA QUE JÁ FUNCIONA"""
    info_paginacao = bot.driver.execute_script("""
        // MESMA LÓGICA QUE JÁ FUNCIONA
        const accordion = document.querySelector('#cdk-accordion-child-2');
        if (!accordion) return { tem_proxima: false, motivo: 'Accordion não encontrado' };
        
        const nextButtons = accordion.querySelectorAll('button.mat-paginator-navigation-next');
        for (let btn of nextButtons) {
            if (!btn.disabled && btn.getAttribute('aria-disabled') !== 'true') {
                return { tem_proxima: true };
            }
        }
        return { tem_proxima: false };
    """)
    
    if info_paginacao.get('tem_proxima'):
        sucesso = bot.driver.execute_script("""
            // MESMA LÓGICA QUE JÁ FUNCIONA
            const accordion = document.querySelector('#cdk-accordion-child-2');
            if (!accordion) return false;
            
            const nextButtons = accordion.querySelectorAll('button.mat-paginator-navigation-next');
            for (let btn of nextButtons) {
                if (!btn.disabled && btn.getAttribute('aria-disabled') !== 'true') {
                    btn.click();
                    return true;
                }
            }
            return false;
        """)
        
        if sucesso:
            sleep(2)
            return True
    
    return False


def ir_para_primeira_pagina_sempre(bot):
    """Vai para a primeira página - MESMA LÓGICA DA PAGINAÇÃO"""
    print("   🔄 Indo para PRIMEIRA página...")
    
    # ESTRATÉGIA 1: MESMA LÓGICA DA PAGINAÇÃO
    print("   🔄 Tentando método DIRETO no botão 'Primeira'...")
    sucesso_direto = bot.driver.execute_script("""
        // MESMA LÓGICA: buscar no accordion correto
        const accordion = document.querySelector('#cdk-accordion-child-2');
        if (!accordion) return false;
        
        const firstButtons = accordion.querySelectorAll('button.mat-paginator-navigation-first');
        
        for (let btn of firstButtons) {
            try {
                // MESMA LÓGICA: clicar como na paginação
                btn.click();
                return true;
            } catch (e) {
                // Tentar método alternativo
                btn.dispatchEvent(new Event('click', { bubbles: true }));
                return true;
            }
        }
        return false;
    """)
    
    if sucesso_direto:
        sleep(3)
        print("   ✅ Primeira página carregada (via botão)")
        return True
    
    # ESTRATÉGIA 2: MÚLTIPLOS CLICKS no "Anterior" - MESMA LÓGICA
    print("   🔄 Tentando método AGGRESSIVO (múltiplos 'Anterior')...")
    for tentativa in range(20):
        # Verificar se já está na primeira - MESMA LÓGICA
        esta_na_primeira = bot.driver.execute_script("""
            const accordion = document.querySelector('#cdk-accordion-child-2');
            if (!accordion) return false;
            
            const prevButtons = accordion.querySelectorAll('button.mat-paginator-navigation-previous');
            for (let btn of prevButtons) {
                if (btn.disabled || btn.getAttribute('aria-disabled') === 'true') {
                    return true;
                }
            }
            return false;
        """)
        
        if esta_na_primeira:
            print(f"   ✅ Chegou na primeira página após {tentativa} cliques 'Anterior'")
            return True
        
        # Clicar no "Anterior" - MESMA LÓGICA
        clique_anterior = bot.driver.execute_script("""
            const accordion = document.querySelector('#cdk-accordion-child-2');
            if (!accordion) return false;
            
            const prevButtons = accordion.querySelectorAll('button.mat-paginator-navigation-previous');
            for (let btn of prevButtons) {
                if (!btn.disabled && btn.getAttribute('aria-disabled') !== 'true') {
                    btn.click();
                    return true;
                }
            }
            return false;
        """)
        
        if clique_anterior:
            sleep(1)
            print(f"   ↩️  Clicou 'Anterior'... ({tentativa + 1}/20)")
        else:
            print("   ❌ Botão 'Anterior' não disponível")
            break
    
    print("   ⚠️  Não conseguiu resetar completamente, mas continuando...")
    return False # Mesmo falhando, continua a busca

def buscar_e_marcar_nf(bot, nf_procurada):
    """Busca e marca uma NF - MESMA LÓGICA DA PAGINAÇÃO"""
    print(f"   🔍 Buscando NF {nf_procurada}...")
    
    # VERIFICAR PAGINA ATUAL ANTES DO RESET
    pagina_antes = bot.driver.execute_script("""
        // Mesma lógica da paginação - buscar no accordion correto
        const accordion = document.querySelector('#cdk-accordion-child-2');
        if (!accordion) return 'Accordion não encontrado';
        
        const paginator = accordion.querySelector('mat-paginator');
        if (!paginator) return 'Paginador não encontrado';
        
        const rangeLabel = paginator.querySelector('.mat-paginator-range-label');
        return rangeLabel ? rangeLabel.textContent.trim() : 'Range não encontrado';
    """)
    print(f"   📍 Página antes do reset: {pagina_antes}")
    
    # RESET AGRESSIVO - MESMA LÓGICA DA PAGINAÇÃO
    print("   🔄 RESET AGRESSIVO da paginação...")
    ir_para_primeira_pagina_sempre(bot)
    
    # VERIFICAR PAGINA ATUAL DEPOIS DO RESET
    pagina_depois = bot.driver.execute_script("""
        const accordion = document.querySelector('#cdk-accordion-child-2');
        if (!accordion) return 'Accordion não encontrado';
        
        const paginator = accordion.querySelector('mat-paginator');
        if (!paginator) return 'Paginador não encontrado';
        
        const rangeLabel = paginator.querySelector('.mat-paginator-range-label');
        return rangeLabel ? rangeLabel.textContent.trim() : 'Range não encontrado';
    """)
    print(f"   📍 Página depois do reset: {pagina_depois}")
    
    pagina_atual = 1
    total_paginas_percorridas = 0
    
    while total_paginas_percorridas < 10:
        print(f"   📄 Verificando página {pagina_atual}...")
        
        # Busca na TABELA CORRETA - MESMA LÓGICA DA PAGINAÇÃO
        resultado_busca = bot.driver.execute_script("""
            const nfProcurada = '""" + nf_procurada + """';
            
            // MESMA LÓGICA: buscar no accordion correto
            const accordion = document.querySelector('#cdk-accordion-child-2');
            if (!accordion) {
                return { encontrada: false, motivo: 'Accordion não encontrado' };
            }
            
            const tabela = accordion.querySelector('table');
            if (!tabela) {
                return { encontrada: false, motivo: 'Tabela não encontrada' };
            }
            
            const linhas = tabela.querySelectorAll('tbody tr');
            
            for (let i = 0; i < linhas.length; i++) {
                const celulas = linhas[i].querySelectorAll('td');
                
                if (celulas.length >= 11) {
                    const textoNF = celulas[3].textContent.trim();
                    
                    if (textoNF === nfProcurada) {
                        // MESMA LÓGICA: buscar botão DENTRO do accordion correto
                        const botao = celulas[0].querySelector('button[name^="idNotaFiscal_"]');
                        
                        if (botao && !botao.disabled) {
                            // MESMA LÓGICA: clicar como na paginação
                            botao.click();
                            return { 
                                encontrada: true, 
                                marcada: true, 
                                pagina: """ + str(pagina_atual) + """
                            };
                        } else {
                            const motivo = botao ? 'Botão desabilitado' : 'Botão não encontrado';
                            return { 
                                encontrada: true, 
                                marcada: false, 
                                pagina: """ + str(pagina_atual) + """, 
                                motivo: motivo
                            };
                        }
                    }
                }
            }
            return { encontrada: false, pagina: """ + str(pagina_atual) + """ };
        """)
        
        if resultado_busca.get('encontrada'):
            if resultado_busca.get('marcada'):
                print(f"      ✅ ENCONTRADA e MARCADA na página {pagina_atual}!")
                return {'encontrada': True, 'marcada': True, 'pagina': pagina_atual}
            else:
                print(f"      ⚠️  ENCONTRADA mas não marcada na página {pagina_atual}: {resultado_busca.get('motivo')}")
                return {'encontrada': True, 'marcada': False, 'pagina': pagina_atual, 'motivo': resultado_busca.get('motivo')}
        else:
            print(f"      ❌ Não encontrada na página {pagina_atual}")
            
            # MESMA LÓGICA: usar a função de paginação que já funciona
            if verificar_proxima_pagina(bot):
                pagina_atual += 1
                total_paginas_percorridas += 1
                print(f"      ➡️  Indo para página {pagina_atual}...")
            else:
                print(f"      🏁 Fim das páginas (última: {pagina_atual})")
                break
    
    return {'encontrada': False, 'marcada': False, 'motivo': 'NF não encontrada'}

def processar_nfs_inteligente(bot, nfs_excel):
    """Processa cada NF do Excel de forma inteligente"""
    print(f"\n🎯 INICIANDO BUSCA INTELIGENTE...")
    print(f"   📋 {len(nfs_excel)} NFs para processar")
    print("=" * 50)
    
    nfs_marcadas = 0
    nfs_nao_encontradas = []
    nfs_com_problema = []
    
    for i, nf in enumerate(nfs_excel, 1):
        print(f"\n[{i}/{len(nfs_excel)}] 🎯 PROCESSANDO NF: {nf}")
        print("-" * 40)
        
        # Buscar e marcar a NF (SEMPRE começa da página 1)
        resultado = buscar_e_marcar_nf(bot, nf)
        
        if resultado.get('encontrada'):
            if resultado.get('marcada'):
                nfs_marcadas += 1
                sleep(0.5)  # Pequena pausa entre marcações
            else:
                nfs_com_problema.append((nf, resultado.get('motivo', 'Motivo desconhecido')))
        else:
            nfs_nao_encontradas.append(nf)
    
    return nfs_marcadas, nfs_nao_encontradas, nfs_com_problema

def test_fluxo_paginacao_corrigido():
    # Carregar dados do Excel
    XLSX = r"C:\Users\sousa.lima\Documents\Projetos\ApiAutomation\API_AUTOMATION\APP\Data\FIDC CAP DIARIO.xlsx"
    SHEET = "FIDC Contas a pagar."
    
    print("📊 CARREGANDO DADOS DO EXCEL...")
    mapa = mapear_emps_para_nfs(XLSX, SHEET)
    
    bot = SeleniumIntegration(timeout=40)
    
    try:
        # 1) Login
        print("\n🔐 FAZENDO LOGIN...")
        bot.login(LoginDTO(
            usuario="42549981391", 
            senha="cariri1627"
        ), url="https://web.accesstage.com.br/santander-montadoras-ui/#/login")
        sleep(3)
        
        # 2) Navegação
        print("📂 ACESSANDO MÓDULO FIDC...")
        bot.clica_no_modulo_fidc(text_hint="Módulo FIDC")
        bot.clica_em_aberto()
        sleep(3)
        
        print(f"🔗 Página atual: {bot.driver.current_url}")
        
        # 3) IDENTIFICAR TABELA
        print("\n🔍 CONFIGURANDO TABELA...")
        print("   ✅ Usando tabela índice: 0 (Títulos Em Aberto)")
        
        emp = "TA"
        if emp in mapa:
            nfs_excel = mapa[emp]
            print(f"\n🏢 EMPRESA: {emp}")
            print(f"   📋 NFs do Excel: {nfs_excel}")
            
            # 4) FAZER PESQUISA
            print("🔄 INICIANDO PESQUISA...")
            resultado_pesquisa = fazer_pesquisa_com_autocomplete(bot)
            if not resultado_pesquisa.get('sucesso'):
                print(f"❌ Falha na pesquisa: {resultado_pesquisa.get('motivo')}")
                return
            
            # 5) PROCESSAR NFs
            nfs_marcadas, nfs_nao_encontradas, nfs_com_problema = processar_nfs_inteligente(bot, nfs_excel)
            
            # 6) RELATÓRIO FINAL
            print(f"\n🎉 RELATÓRIO FINAL")
            print("=" * 50)
            print(f"📊 RESULTADOS:")
            print(f"   • NFs do Excel: {len(nfs_excel)}")
            print(f"   • NFs marcadas: {nfs_marcadas}")
            print(f"   • NFs não encontradas: {len(nfs_nao_encontradas)}")
            print(f"   • NFs com problema: {len(nfs_com_problema)}")
            
            if nfs_nao_encontradas:
                print(f"\n📋 NFs NÃO ENCONTRADAS:")
                for nf in nfs_nao_encontradas:
                    print(f"   • {nf}")
            
            if nfs_com_problema:
                print(f"\n⚠️  NFs COM PROBLEMA:")
                for nf, motivo in nfs_com_problema:
                    print(f"   • {nf} - {motivo}")
            
            eficiencia = (nfs_marcadas / len(nfs_excel)) * 100 if nfs_excel else 0
            print(f"\n💡 EFICIÊNCIA: {eficiencia:.1f}%")
            
            if nfs_marcadas == len(nfs_excel):
                print("   🎉 TODAS as NFs do Excel foram marcadas!")
            elif nfs_marcadas > 0:
                print(f"   ✅ {nfs_marcadas} NFs marcadas com sucesso")
            else:
                print("   ❌ Nenhuma NF do Excel foi encontrada")
        
        print(f"\n🎉 PROCESSO CONCLUÍDO!")
        
        print("\n🔍 Browser mantido aberto para verificação...")
        input("⏸️  Pressione Enter para fechar...")
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n🔍 Browser mantido aberto para debug...")
        input("⏸️  Pressione Enter para fechar...")
    finally:


        bot.close()

if __name__ == "__main__":
    test_fluxo_paginacao_corrigido()



