from flask import request, current_app
from flask_restx import Namespace, Resource
from selenium_runner import quick_visit
import os

selenium_ns = Namespace("teste", description="Testes Selenium")

@selenium_ns.route("/testeWebdriver")
class TesteWebdriver(Resource):
    def get(self):
        try:
            url = request.args.get("url", "https://example.com")
            return quick_visit(url), 200
        except Exception as e:
            current_app.logger.exception("Falha em /teste/testeWebdriver")
            return {"ok": False, "error": str(e)}, 200

@selenium_ns.route("/diag")
class SeleniumDiag(Resource):
    def get(self):
        chrome = os.getenv("CHROME_BIN", "/usr/bin/chromium")
        driver = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
        return {
            "chrome": chrome,
            "driver": driver,
            "chrome_exists": os.path.exists(chrome),
            "driver_exists": os.path.exists(driver),
        }, 200
