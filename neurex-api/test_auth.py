
from jose import jwt

from api.routes.auth import ALGORITHM, SECRET_KEY

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3NzI0MDczOX0.TQcFswUGBxb-HmuLi7oceOrXjartV2NP8eDsV8BbgLg"
print(f"Secret: {SECRET_KEY}")
print(f"Algo: {ALGORITHM}")

try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print(f"Payload: {payload}")
except Exception as e:
    print(f"Error: {e}")
