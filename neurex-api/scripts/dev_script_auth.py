import os

from jose import jwt

from api.routes.auth import ALGORITHM, SECRET_KEY

token = os.getenv("NEUREX_DEV_TOKEN", "")
print("Decoding token using active security algorithm...")

if token:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("Success: Token is valid.")
    except Exception as e:
        print("Error: Invalid token or secret.")
else:
    print("No token provided. Set NEUREX_DEV_TOKEN to test.")
