from flask_restx import Namespace, Resource
from APP.Services.teste_selenium import SeleniumTest

selenium_ns = Namespace("teste", description="Teste Selenium")


@selenium_ns.route("/testeWebdriver")
class TesteWebdriver(Resource):
    def get(self):
        automation = SeleniumTest()
        automation.driver.get("https://www.google.com")
        return {"ok": True}, 200