from pathlib import Path

import uvicorn
from connexion import AsyncApp, RestyResolver

from config import load_config

#import time

#from jose import jwt

app = AsyncApp(__name__)

app.add_api('api/v1/openapi.yaml', base_path='/api/v1', resolver=RestyResolver("api.v1"))

working_directory = load_config()["working_directory"]

Path(working_directory).mkdir(parents=True, exist_ok=True)


#JWT_ISSUER = "com.vmbytsko.gallery"
#JWT_SECRET = "12354"
#JWT_LIFETIME_SECONDS = 600
#JWT_ALGORITHM = "HS256"

#def _current_timestamp() -> int:
#    return int(time.time())

#def generate_token(user_id):
#    timestamp = _current_timestamp()
#    payload = {
#        "iss": JWT_ISSUER,
#        "iat": int(timestamp),
#        "exp": int(timestamp + JWT_LIFETIME_SECONDS),
#        "sub": str(user_id),
#    }
#
#    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

#def decode_token(token):
#    try:
#        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
#    except:
#        pass

#def get_secret(user, token_info) -> str:
#    return """
#    You are user_id {user} and the secret is 'wbevuec' циумгул.
#    Decoded token claims: {token_info}.
#    """.format(
#        user=user, token_info=token_info
#    )


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
