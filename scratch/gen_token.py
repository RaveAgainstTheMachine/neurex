import os
from datetime import timedelta
from jose import jwt
from datetime import datetime, UTC

def create_eval_token():
    secret = os.getenv("JWT_SECRET", "neurex-dev-stable-secret-123")
    algorithm = "HS256"
    expire = datetime.now(UTC) + timedelta(minutes=60)
    to_encode = {"sub": "eval_runner", "exp": expire}
    return jwt.encode(to_encode, secret, algorithm=algorithm)

if __name__ == "__main__":
    print(create_eval_token())
