class Paths:
    class Url:
        url = "https://web.accesstage.com.br/santander-montadoras-ui/#/login"

    class Login:
        username = "//input[@formcontrolname='username' or @type='text' or contains(@id, 'mat-input')]"
        password = "//input[@formcontrolname='password' or @type='password']"
        submit   = "//button[@type='submit' or contains(., 'Entrar') or contains(., 'Login')]"

    class HomePage:
        div_login     = "//a[contains(@class, 'nav-link') and contains(., 'Sair')]"
        modulo_fidc = "//a[contains(., 'FloorPlan') or contains(., 'FIDC')]"
        btn_em_aberto = "//a[contains(., 'Em aberto') or contains(., 'Aberto')]"
    
    class OutstandingTitles:
        div_central = "//div[contains(@class, 'container') or contains(@class, 'main-content')]"
        div_boletos_gerados = "//div[contains(., 'Boletos Gerados')]"
        div_titulos_abertos = "//div[contains(., 'Títulos em Aberto')]"
        itens_per_page = "//mat-select[contains(@id, 'paginator')]"
        div_alerta_boleto_aberto  = "//div[contains(@class, 'mat-dialog')]"
    
    class Tabelas:
        tabela_titulos_abertos = "//table//tbody"

    class Inputs:
        input_revenda = "//input[contains(@placeholder, 'Revenda') or contains(@formcontrolname, 'revenda')]"
        itens_por_pagina = "//mat-select[contains(@id, 'paginator')]"
        btn_pesquisar = "//button[contains(., 'Pesquisar')]"
        btn_fechar = "//button[contains(., 'Fechar') or contains(@class, 'close')]"