# APP/Controllers/controller_teste.py
from flask_restx import Namespace, Resource
from APP.Services.teste_selenium import SeleniumTest

selenium_ns = Namespace("teste", description="Teste Selenium")

@selenium_ns.route("/testeWebdriver")
class TesteWebdriver(Resource):
    def get(self):
        try:
            bot = SeleniumTest()
            try:
                title = bot.get("https://www.google.com")
                return {"ok": True, "title": title}, 200
            finally:
                bot.quit()
        except Exception as e:
            # 500 com detalhe do erro (temporário p/ diagnóstico)
            return {"ok": False, "error": str(e)}, 500
