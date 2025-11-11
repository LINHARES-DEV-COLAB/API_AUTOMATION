from time import sleep

from APP.Config.fidc_trata_emp import TrataEmpresa

def fazer_pesquisa_com_autocomplete(bot, emp: str):
    """Faz a pesquisa incluindo a seleção do autocomplete - VERSÃO CORRIGIDA"""
    print("🔄 FAZENDO PESQUISA COM AUTOCOMPLETE...")
    empresaTratada = TrataEmpresa.trataEmp(emp)
    
    # 1) Primeiro encontrar e focar no campo Revenda
    campo_encontrado = bot.driver.execute_script("""
        // Procura o campo Revenda de forma mais robusta
        const selectors = [
            'input[placeholder="Revenda"]',
            'input[aria-label="Revenda"]',
            'input[formcontrolname*="revenda" i]',
            'input[matinput][placeholder*="revenda" i]'
        ];
        
        for (const selector of selectors) {
            const campo = document.querySelector(selector);
            if (campo) {
                campo.focus();
                campo.value = '';
                return {sucesso: true, campo: selector};
            }
        }
        return {sucesso: false, motivo: 'Campo Revenda não encontrado'};
    """)
    
    if not campo_encontrado.get('sucesso'):
        return campo_encontrado
    
    print("✅ Campo Revenda encontrado")
    
    # 2) Digitar o texto gradualmente para trigger do autocomplete
    texto_empresa = empresaTratada.emp
    resultado_digitacao = bot.driver.execute_script("""
        const texto = arguments[0];
        const campo = document.querySelector('input[placeholder="Revenda"]');
        
        if (!campo) return {sucesso: false, motivo: 'Campo perdido após foco'};
        
        // Digita caractere por caractere para simular usuário
        for (let i = 0; i < texto.length; i++) {
            campo.value = texto.substring(0, i + 1);
            
            // Dispara todos os eventos necessários
            campo.dispatchEvent(new Event('input', { bubbles: true }));
            campo.dispatchEvent(new Event('keydown', { bubbles: true }));
            campo.dispatchEvent(new Event('keyup', { bubbles: true }));
            campo.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        // Foca novamente para garantir que autocomplete abra
        campo.focus();
        campo.click();
        
        return {sucesso: true, texto_inserido: texto};
    """, texto_empresa)
    
    if not resultado_digitacao.get('sucesso'):
        return resultado_digitacao
    
    print(f"✅ Texto '{texto_empresa}' digitado no campo Revenda")
    
    # 3) Aguardar o autocomplete carregar
    sleep(3)
    
    # 4) Buscar e clicar na opção do autocomplete - VERSÃO CORRIGIDA
    autocomplete_clicado = bot.driver.execute_script("""
        const textoProcurado = arguments[0];
        
        // Estratégia 1: Procurar no overlay do autocomplete (quando aberto)
        const autocompletePanels = document.querySelectorAll('div.mat-autocomplete-panel');
        for (let panel of autocompletePanels) {
            const opcoes = panel.querySelectorAll('mat-option');
            for (let opcao of opcoes) {
                const textoOpcao = opcao.textContent.trim();
                if (textoOpcao.includes(textoProcurado)) {
                    opcao.click();
                    return {sucesso: true, metodo: 'overlay', texto: textoOpcao};
                }
            }
        }
        
        // Estratégia 2: Procurar em qualquer mat-option visível na página
        const todasOpcoes = document.querySelectorAll('mat-option');
        for (let opcao of todasOpcoes) {
            // Verificar se a opção está visível (autocomplete aberto)
            const estilo = window.getComputedStyle(opcao);
            if (estilo.display !== 'none' && estilo.visibility !== 'hidden') {
                const textoOpcao = opcao.textContent.trim();
                if (textoOpcao.includes(textoProcurado)) {
                    opcao.click();
                    return {sucesso: true, metodo: 'visivel', texto: textoOpcao};
                }
            }
        }
        
        // Estratégia 3: Tentar usar keyboard navigation
        const campo = document.querySelector('input[placeholder="Revenda"]');
        if (campo) {
            // Abre o autocomplete se não estiver aberto
            campo.dispatchEvent(new KeyboardEvent('keydown', { 
                key: 'ArrowDown', 
                code: 'ArrowDown',
                keyCode: 40,
                bubbles: true 
            }));
            
            // Aguarda um pouco e tenta pegar a primeira opção
            setTimeout(() => {
                const primeiraOpcao = document.querySelector('mat-option');
                if (primeiraOpcao) {
                    primeiraOpcao.click();
                    return {sucesso: true, metodo: 'keyboard', texto: primeiraOpcao.textContent.trim()};
                }
            }, 500);
        }
        
        return {sucesso: false, motivo: 'Nenhuma opção do autocomplete encontrada'};
    """, texto_empresa)
    
    # Verificar o resultado do autocomplete
    if autocomplete_clicado and autocomplete_clicado.get('sucesso'):
        print(f"✅ Opção selecionada: {autocomplete_clicado.get('texto')} (método: {autocomplete_clicado.get('metodo')})")
        sleep(1)
    else:
        print("⚠️  Autocomplete não encontrado, continuando com o texto digitado...")
        # Não falha aqui, continua com o texto que já está no campo
    
    # 5) Clicar no botão Pesquisar
    pesquisar_clicado = bot.driver.execute_script("""
        // Procura o botão Pesquisar
        const botoes = document.querySelectorAll('button');
        for (let botao of botoes) {
            const textoBotao = botao.textContent.trim();
            if (textoBotao.includes('Pesquisar') && !botao.disabled) {
                botao.click();
                return {sucesso: true, texto: textoBotao};
            }
        }
        return {sucesso: false, motivo: 'Botão Pesquisar não encontrado'};
    """)
    
    if pesquisar_clicado and pesquisar_clicado.get('sucesso'):
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

def processar_nfs_com_limite_valor(bot, nfs_excel, limite_valor=250000):
    """Processa NFs em batches baseado no limite de valor (250k por boleto)"""
    print(f"\n💰 PROCESSANDO NFS COM LIMITE DE VALOR: R$ {limite_valor:,.2f}")
    print(f"   📋 {len(nfs_excel)} NFs para processar")
    print("=" * 60)
    
    resultados = {
        'boletos_gerados': 0,
        'nfs_processadas': 0,
        'nfs_nao_encontradas': [],
        'nfs_com_problema': [],
        'batches': []
    }
    
    # 1) PRIMEIRO: COLETAR VALORES DE TODAS AS NFs
    print("🔍 COLETANDO VALORES DAS NFs...")
    nfs_com_valores = []
    
    for i, nf in enumerate(nfs_excel, 1):
        print(f"   [{i}/{len(nfs_excel)}] Coletando valor da NF: {nf}")
        
        # Buscar a NF e coletar seu valor
        info_nf = buscar_e_coletar_valor_nf(bot, nf)
        
        if info_nf.get('encontrada'):
            if info_nf.get('valor'):
                nfs_com_valores.append({
                    'nf': nf,
                    'valor': info_nf['valor'],
                    'pagina': info_nf.get('pagina', 1)
                })
                print(f"      ✅ Valor: R$ {info_nf['valor']:,.2f}")
            else:
                resultados['nfs_com_problema'].append((nf, 'Valor não encontrado'))
                print(f"      ⚠️  Valor não encontrado")
        else:
            resultados['nfs_nao_encontradas'].append(nf)
            print(f"      ❌ NF não encontrada")
    
    print(f"📊 RESUMO DA COLETA:")
    print(f"   • NFs com valores: {len(nfs_com_valores)}")
    print(f"   • NFs não encontradas: {len(resultados['nfs_nao_encontradas'])}")
    print(f"   • Valor total: R$ {sum(nf['valor'] for nf in nfs_com_valores):,.2f}")
    
    # 2) AGRUPAR NFs EM BATCHES ATÉ 250k
    batches = agrupar_nfs_em_batches(nfs_com_valores, limite_valor)
    
    print(f"📦 BATCHES CRIADOS: {len(batches)}")
    for i, batch in enumerate(batches, 1):
        valor_batch = sum(nf['valor'] for nf in batch['nfs'])
        print(f"   • Batch {i}: {len(batch['nfs'])} NFs - R$ {valor_batch:,.2f}")
    
    # 3) PROCESSAR CADA BATCH
    for batch_num, batch in enumerate(batches, 1):
        print(f"\n🎯 PROCESSANDO BATCH {batch_num}/{len(batches)}")
        print(f"   📋 {len(batch['nfs'])} NFs - Valor total: R$ {batch['valor_total']:,.2f}")
        
        # Reset para primeira página
        ir_para_primeira_pagina_sempre(bot)
        
        # Marcar todas as NFs do batch
        nfs_marcadas_no_batch = []
        
        for nf_info in batch['nfs']:
            nf = nf_info['nf']
            print(f"   🔘 Marcando NF: {nf} (R$ {nf_info['valor']:,.2f})")
            
            resultado_marcacao = marcar_nf_especifica(bot, nf)
            
            if resultado_marcacao.get('marcada'):
                nfs_marcadas_no_batch.append(nf_info)
                print(f"      ✅ Marcada")
                sleep(0.5)
            else:
                print(f"      ❌ Falha na marcação")
        
        # Se marcou alguma NF no batch, gerar boleto
        if nfs_marcadas_no_batch:
            print(f"   🧾 GERANDO BOLETO PARA {len(nfs_marcadas_no_batch)} NFs...")
            
            if gerar_boleto(bot):
                resultados['boletos_gerados'] += 1
                resultados['nfs_processadas'] += len(nfs_marcadas_no_batch)
                resultados['batches'].append({
                    'numero': batch_num,
                    'nfs': nfs_marcadas_no_batch,
                    'valor_total': sum(nf['valor'] for nf in nfs_marcadas_no_batch),
                    'status': 'sucesso'
                })
                print(f"      ✅ Boleto gerado com sucesso!")
            else:
                resultados['batches'].append({
                    'numero': batch_num,
                    'nfs': nfs_marcadas_no_batch,
                    'valor_total': sum(nf['valor'] for nf in nfs_marcadas_no_batch),
                    'status': 'erro_geracao'
                })
                print(f"      ❌ Falha ao gerar boleto")
        else:
            print(f"   ⚠️  Nenhuma NF marcada neste batch")
    
    return resultados

def buscar_e_coletar_valor_nf(bot, nf_procurada):
    """Busca uma NF específica e coleta seu valor"""
    print(f"   🔍 Buscando e coletando valor da NF {nf_procurada}...")
    
    # Reset para primeira página
    ir_para_primeira_pagina_sempre(bot)
    
    pagina_atual = 1
    total_paginas_percorridas = 0
    
    while total_paginas_percorridas < 10:
        resultado_busca = bot.driver.execute_script("""
            const nfProcurada = '""" + nf_procurada + """';
            
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
                        // Coletar o valor do boleto (coluna 8 - Valor do Boleto)
                        const valorTexto = celulas[8].textContent.trim();
                        
                        // Converter "R$ 19.542,51" para 19542.51
                        let valorNumerico = 0;
                        try {
                            const valorLimpo = valorTexto.replace('R$', '').replace('.', '').replace(',', '.').trim();
                            valorNumerico = parseFloat(valorLimpo);
                        } catch (e) {
                            return { 
                                encontrada: true, 
                                valor: null, 
                                motivo: 'Erro ao converter valor: ' + valorTexto
                            };
                        }
                        
                        return { 
                            encontrada: true, 
                            valor: valorNumerico,
                            pagina: """ + str(pagina_atual) + """,
                            linha: i
                        };
                    }
                }
            }
            return { encontrada: false, pagina: """ + str(pagina_atual) + """ };
        """)
        
        if resultado_busca.get('encontrada'):
            return resultado_busca
        
        # Tentar próxima página
        if verificar_proxima_pagina(bot):
            pagina_atual += 1
            total_paginas_percorridas += 1
        else:
            break
    
    return {'encontrada': False, 'motivo': 'NF não encontrada'}

def agrupar_nfs_em_batches(nfs_com_valores, limite_valor):
    """Agrupa NFs em batches baseado no limite de valor"""
    batches = []
    batch_atual = []
    valor_batch_atual = 0
    
    # Ordenar NFs por valor (opcional - pode ajudar na otimização)
    nfs_ordenadas = sorted(nfs_com_valores, key=lambda x: x['valor'], reverse=True)
    
    for nf_info in nfs_ordenadas:
        valor_nf = nf_info['valor']
        
        # Se adicionar esta NF ultrapassar o limite (e o batch não está vazio)
        if batch_atual and (valor_batch_atual + valor_nf) > limite_valor:
            # Fechar batch atual e começar novo
            batches.append({
                'nfs': batch_atual.copy(),
                'valor_total': valor_batch_atual
            })
            batch_atual = []
            valor_batch_atual = 0
        
        # Adicionar NF ao batch atual
        batch_atual.append(nf_info)
        valor_batch_atual += valor_nf
    
    # Adicionar o último batch se não estiver vazio
    if batch_atual:
        batches.append({
            'nfs': batch_atual,
            'valor_total': valor_batch_atual
        })
    
    return batches

def marcar_nf_especifica(bot, nf):
    """Marca uma NF específica (versão simplificada da busca)"""
    resultado = bot.driver.execute_script("""
        const nfProcurada = '""" + nf + """';
        
        const accordion = document.querySelector('#cdk-accordion-child-2');
        if (!accordion) return { marcada: false, motivo: 'Accordion não encontrado' };
        
        const tabela = accordion.querySelector('table');
        if (!tabela) return { marcada: false, motivo: 'Tabela não encontrada' };
        
        const linhas = tabela.querySelectorAll('tbody tr');
        
        for (let i = 0; i < linhas.length; i++) {
            const celulas = linhas[i].querySelectorAll('td');
            
            if (celulas.length >= 11) {
                const textoNF = celulas[3].textContent.trim();
                
                if (textoNF === nfProcurada) {
                    const botao = celulas[0].querySelector('button[name^="idNotaFiscal_"]');
                    
                    if (botao && !botao.disabled) {
                        botao.click();
                        return { marcada: true, linha: i };
                    } else {
                        const motivo = botao ? 'Botão desabilitado' : 'Botão não encontrado';
                        return { marcada: false, motivo: motivo };
                    }
                }
            }
        }
        return { marcada: false, motivo: 'NF não encontrada na página atual' };
    """)
    
    return resultado

def gerar_boleto(bot):
    """Clica no botão para gerar boleto dos itens selecionados"""
    print("   🖨️  Clicando no botão de gerar boleto...")
    
    resultado = bot.driver.execute_script("""
        // Procurar o botão de gerar boleto - pode ser por ícone PDF ou texto
        const botoes = document.querySelectorAll('button');
        
        for (let botao of botoes) {
            const textoBotao = botao.textContent.trim();
            const ariaLabel = botao.getAttribute('aria-label') || '';
            const tooltip = botao.getAttribute('mattooltip') || '';
            
            // Verificar se é botão de gerar boleto/PDF
            if ((textoBotao.includes('Gerar') && textoBotao.includes('Boleto')) ||
                ariaLabel.includes('PDF') || 
                tooltip.includes('PDF') ||
                textoBotao.includes('PDF')) {
                
                if (!botao.disabled) {
                    botao.click();
                    return { sucesso: true, tipo: 'texto', texto: textoBotao };
                } else {
                    return { sucesso: false, motivo: 'Botão desabilitado' };
                }
            }
        }
        
        // Fallback: procurar por ícone de PDF
        const iconesPDF = document.querySelectorAll('img[src*="pdf"]');
        for (let icone of iconesPDF) {
            const botaoPai = icone.closest('button');
            if (botaoPai && !botaoPai.disabled) {
                botaoPai.click();
                return { sucesso: true, tipo: 'icone' };
            }
        }
        
        return { sucesso: false, motivo: 'Botão de gerar boleto não encontrado' };
    """)
    
    if resultado.get('sucesso'):
        print(f"      ✅ Botão clicado (tipo: {resultado.get('tipo')})")
        sleep(3)  # Aguardar geração do boleto
        return True
    else:
        print(f"      ❌ {resultado.get('motivo')}")
        return False



