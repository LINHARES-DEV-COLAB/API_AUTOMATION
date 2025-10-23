class Path:
    class Url:
        url='https://www3.honda.com.br/corp/ihs/portal/#/login'
    
    class Login:
        campo_code='div.form-group input#codEmpresa.form-control'
        campo_user='div.form-group input#codUsuario.form-control'
        campo_password='div.form-group input#senha.form-control'
        btn_entrar='form#formLogin button#submitLogin.btn.btn-default'
        btn_prosseguir='div.div-token center button.btn-default.btn.button-token'
        alterar_senha='div#app div.container h1'  # Verificar se o texto é "Alterar Senha"
        senha_incorreta='div#app div.footAlert button'  # Veficar o texto "Fechar"
    
    class Logout:
        btn_sair='div.pull-right div.logout a'
    
    class MenuPrincipal:
        # Todos esses deve ser visto o texto
        aba_consorcio='div.panel-heading h4 a.a-empresaHonda'
        aba_formularios_download='div.menugeral ul li a'
        aba_consorcio_side_menu='div#sideMenu0.collapse.in div.itemMenu a.parent.list-group-item.list-group-item-success'
        aba_solicitacao_carga='div.itemMenu a'
        inicio='div#container-portal div.breadcrumb h4 span a'
        btn_mensagem='div#container-portal button[type="submit"]'
    
    class Frame:
        id_linha_ccc='table#Grid2ContainerTbl tbody tr#Grid2ContainerRow'  # Usar randomico para  _0001
        id_link_ccc='span#span_vDESCREG'  # Usar randomico para  _0001
        btn_baixar='table#TABLE2_MPAGE table#T_CONFIRMA tbody tr td input'  # Clicar pelo atributo value ok
    
    class Janela:
        input_inicio='input#vDTINI'
        input_fim='input#vDTFIN'
        btn_confirmar='table#TABLE1 tbody tr td input'  # Texto "Confirmar"
        btn_imprimir='table#TABLE10 tbody tr td input'  # Texto "Imprimir"