from pathlib import Path
from secrets import token_urlsafe

from config import get_config


class JWTSettings:
    def __init__(self):
        self.jwt_issuer = "com.twicesafe.vault"
        self.jwt_secret = open(get_config().data_directory+"/security/jwt_secret.txt", "r").read()

        if len(self.jwt_secret) == 0:
            raise Exception

        self.jwt_lifetime_seconds = 60 * 60 * 24 * 365  # one year
        self.jwt_algorithm = "HS256"


__cached_jwt_settings: JWTSettings = None

def get_jwt_settings() -> JWTSettings:
    global __cached_jwt_settings
    if __cached_jwt_settings is not None:
        return __cached_jwt_settings

    Path(get_config().data_directory+"/security").mkdir(parents=True, exist_ok=True)
    if not Path(get_config().data_directory+"/security/jwt_secret.txt").is_file():
        with open(get_config().data_directory+"/security/jwt_secret.txt", "w") as f:
            f.write(token_urlsafe(128))
    __cached_jwt_settings = JWTSettings()
    return __cached_jwt_settings
