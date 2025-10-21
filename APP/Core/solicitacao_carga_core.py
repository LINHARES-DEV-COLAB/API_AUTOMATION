class Path:
    class Url:
        url='https://www3.honda.com.br/corp/ihs/portal/#/login'
    
    class Login:
        campo_code='div.form-group input#codEmpresa.form-control'
        campo_user='div.form-group input#codUsuario.form-control'
        campo_password='div.form-group input#senha.form-control'
        btn_entrar='form#formLogin button#submitLogin.btn.btn-default'
        btn_prosseguir='div.div-token center button.btn-default.btn.button-token'
    
    class Logout:
        btn_sair='div.pull-right div.logout a'
    
    class MenuPrincipal:
        # Todos esses deve ser visto o texto
        aba_consorcio='div.panel-heading h4 a.a-empresaHonda'
        aba_formularios_download='div.menugeral ul li a'
        aba_consorcio_side_menu='div#sideMenu0.collapse.in div.itemMenu a.parent.list-group-item.list-group-item-success'
        aba_solicitacao_carga='div.itemMenu a'
        btn_mensagem='div#container-portal button[type="submit"]'
    
    class Frame:
        checkbox_ccc='tr#Grid2ContainerRow_0003 input'
        btn_solicitar_carga='table#TABLE1.Table tbody tr td input.BtnEnter'
        entry_de='input#vIH11DINI2'
        entry_a='input#vIH11DFIM2'
        btn_confirmar='table#TABLE1 tbody tr td input.BtnEnter' # Deve verificar o texto