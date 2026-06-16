import os
from jose import jwt
from datetime import datetime, timedelta, UTC

def get_secret_key() -> str:
    key = os.getenv("JWT_SECRET")
    if not key:
        return "neurex-insecure-dev-secret-007"
    return key

ALGORITHM = "HS256"

def create_eval_token():
    expire = datetime.now(UTC) + timedelta(hours=24)
    payload = {
        "sub": "eval_runner",
        "exp": expire
    }
    token = jwt.encode(payload, get_secret_key(), algorithm=ALGORITHM)
    print(token)

if __name__ == "__main__":
    create_eval_token()
