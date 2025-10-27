from pdb import run
from flask import request
from flask_restx import Namespace, Resource, fields
from APP.Services.fidc_service import run

from APP.common.protected_resource import ProtectedResource

fidc_ns = Namespace('fidc', description='Emissão de boletos para as montadoreas via FIDC')

@fidc_ns.route('/')
class teste(ProtectedResource):
    def get(self):
        run()
        return {'status': 'FIDC service is healthy'}, 200

