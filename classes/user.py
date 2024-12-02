import sqlite3
import uuid
from enum import Enum
from pathlib import Path
from typing import Self

from jose import jwt

import misc
from config import get_config

config = get_config()

Path(config.data_directory+'/db/').mkdir(parents=True, exist_ok=True)
db = sqlite3.connect(config.data_directory+'/db/users.db', check_same_thread=False)

USERS_TABLE = "UsersV1"
#TODO: db.isolation_level = None

db.execute(f"CREATE TABLE IF NOT EXISTS {USERS_TABLE} (user_id TEXT PRIMARY KEY NOT NULL, status INTEGER NOT NULL, username TEXT NOT NULL, password TEXT NOT NULL)")

class UserDoesntExistException(Exception):
    pass

class UserStatus(Enum):
    DELETED_UNSPECIFIED = -1
    ACTIVE = 0

class User:
    def __init__(self, user_id: str = None, new: bool = False):
        if not new and user_id is None:
            raise Exception("no account_id provided")
        self.user_id = user_id or str(uuid.uuid4())

        if not new:
            cursor = db.execute(f"SELECT * FROM {USERS_TABLE} WHERE user_id = ?", [self.user_id])
            row = cursor.fetchone()
            if row is None:
                cursor.close()
                raise UserDoesntExistException()

            self.status = UserStatus(row[1])
            self.username = row[2]
            self.password = row[3]

            if self.status.value < 0:
                cursor.close()
                raise UserDoesntExistException(f"user with id {self.user_id} bad status {self.status}")

            cursor.close()

    def generate_token(self, device_id: str = None):
        timestamp = misc.current_timestamp()
        payload = {
            "iss": JWT_ISSUER,
            "iat": int(timestamp),
            "exp": int(timestamp + JWT_LIFETIME_SECONDS),
            "sub": self.user_id+"."+(device_id or str(uuid.uuid4())),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def save(self, new: bool = False) -> Self:
        db.execute(
            f"{"INSERT" if new else "REPLACE"} INTO {USERS_TABLE} (user_id, status, username, password) VALUES (?, ?, ?, ?)",
            [self.user_id, self.status.value, self.username, self.password])
        db.commit()
        return self


JWT_ISSUER = "com.vmbytsko.gallery"
JWT_SECRET = "12354"
JWT_LIFETIME_SECONDS = 60 * 60 * 24 * 365  # one year
JWT_ALGORITHM = "HS256"


def login(username: str, password: str) -> str:
    user = get_user_from_username(username)
    return user.generate_token()

def register(username: str, password: str) -> str:
    user = get_user_from_username(username)
    return user.generate_token()

def decode_token(token) -> dict:
    return jwt.decode(token,
                      JWT_SECRET,
                      options={
                          "require_sub": True,
                          "require_iss": True,
                          "require_iat": True,
                          "require_exp": True
                      },
                      algorithms=[JWT_ALGORITHM],
                      issuer=JWT_ISSUER)

def get_user_from_token(token: str) -> User:
    return get_user_from_token_info(decode_token(token))

def get_user_from_token_info(token_info: dict) -> User:
    return User(token_info["sub"].split(".")[0])

def get_user_from_username(username) -> User:
    cursor = db.execute(f"SELECT * FROM {USERS_TABLE} WHERE username = ?", [username])
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        raise UserDoesntExistException()
    return User(row[0])