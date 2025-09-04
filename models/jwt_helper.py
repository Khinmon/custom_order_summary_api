import jwt
import datetime
from odoo import api, SUPERUSER_ID

ALGORITHM = "HS256"

def _secret_key(env):
    return env["ir.config_parameter"].sudo().get_param("jwt.secret", default="change-me")

def generate_jwt(env, payload: dict, expires_in: int = 3600):
    payload = dict(payload)
    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    return jwt.encode(payload, _secret_key(env), algorithm=ALGORITHM)

def verify_jwt(env, token: str):
    if not token:
        return None
    try:
        return jwt.decode(token, _secret_key(env), algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
