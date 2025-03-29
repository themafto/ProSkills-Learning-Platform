import hashlib
import secrets


def generate_password_reset_token():
    token = secrets.token_urlsafe(32)
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    return token, hashed_token
