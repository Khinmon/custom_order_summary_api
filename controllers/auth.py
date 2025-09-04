from odoo import http
from odoo.http import request
from ..models.jwt_helper import generate_jwt

class JwtAuth(http.Controller):

    @http.route('/api/v1/login', type='json', auth='public', methods=['POST'], csrf=False)
    def login(self, **payload):
        data = request.get_json_data()
        login = (data.get("login") or "").strip()
        password = (data.get("password") or "").strip()
        uid = request.session.authenticate(request.db, login, password)
        user = request.env["res.users"].sudo().search([("login", "=", login)], limit=1)
        if not uid:
            return {"error": "invalid_credentials"}
        token = generate_jwt(request.env, {"uid": user.id, "login": user.login}, expires_in=3600)
        return {"token": token}


