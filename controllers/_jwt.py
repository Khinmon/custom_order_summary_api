from odoo.http import request
from functools import wraps
from ..models.jwt_helper import verify_jwt

def jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.httprequest.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return {"error": "missing_or_invalid_authorization"}
        token = auth.split(" ", 1)[1].strip()
        claims = verify_jwt(request.env, token)
        if not claims:
            return {"error": "invalid_or_expired_token"}
        request.jwt_claims = claims
        return fn(*args, **kwargs)
    return wrapper
