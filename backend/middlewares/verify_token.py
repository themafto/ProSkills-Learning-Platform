from fastapi import Cookie, HTTPException
from jose import JWTError, jwt

from backend.oauth2 import ALGORITHM, SECRET_KEY


def verify_access_token(access_token: str = Cookie(None, alias="access_token")):
    if access_token is None:
        raise HTTPException(status_code=401, detail="Access token missing")

    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # payload (email, id, role)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")
