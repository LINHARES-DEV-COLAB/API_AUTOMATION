# APP/Controllers/controller_teste.py
from flask_restx import Namespace, Resource
from APP.Services.teste_selenium import SeleniumTest
from selenium_runner import quick_visit

selenium_ns = Namespace("teste", description="Teste Selenium")

# controller_teste.py
from flask import request
@selenium_ns.route("/testeWebdriver")
class TesteWebdriver(Resource):
    def get(self):
        url = request.args.get("url", "https://example.com")
        return quick_visit(url), 200

