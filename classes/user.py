import json
import uuid
from pathlib import Path
from typing import Self

import jwt
import sqlalchemy
from sqlalchemy import select, Engine
from sqlalchemy.orm import Mapped, mapped_column

import misc
from config import get_config
from security import get_jwt_settings

config = get_config()
jwt_settings = get_jwt_settings()
db: sqlalchemy.orm.session.Session

class UserStatus(misc.IntEnum):
    DELETED_UNSPECIFIED = -1
    ACTIVE = 0

class User(misc.Base):
    __tablename__ = "UsersV1"

    user_id: Mapped[str] = mapped_column(primary_key=True)
    status: Mapped[UserStatus] = mapped_column(misc.IntEnum(UserStatus))
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str]

    def generate_token(self, device_id: str = None):
        timestamp = misc.current_timestamp()
        payload = {
            "iss": jwt_settings.jwt_issuer,
            "iat": int(timestamp),
            "exp": int(timestamp + jwt_settings.jwt_lifetime_seconds),
            "sub": self.user_id + "." + (device_id or str(uuid.uuid4())),
        }
        return jwt.encode(payload, jwt_settings.jwt_secret, algorithm=jwt_settings.jwt_algorithm)

    def get_head(self, repository_name):
        folder_path = get_config().data_directory + "/usercommits/v1/" + self.user_id + "/v1/"+repository_name
        head_path = folder_path+"/HEAD"
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        if not Path(head_path).is_file():
            return None
        return open(head_path, "r").read()

    def add_commit(self, repository_name: str, commit: dict):
        folder_path = get_config().data_directory + "/usercommits/v1/" + self.user_id + "/v1/" + repository_name

        Path(folder_path).mkdir(parents=True, exist_ok=True)

        commit_id = str(uuid.uuid4())
        commit_path = folder_path + "/" + commit_id
        while Path(
                commit_path).is_file():
            commit_id = str(uuid.uuid4())
            commit_path = folder_path + "/" + commit_id

        open(commit_path, "w").write(json.dumps(commit))

        return commit_id

    def save(self, new: bool = False):
        try:
            if new:
                db.add(self)
            else:
                db.merge(self)
        except:
            db.rollback()
            raise
        else:
            db.commit()

    def __repr__(self) -> str:
        return f"User(user_id={self.user_id})"

    def __eq__(self, other: Self):
        return self.user_id == other.user_id


def decode_token(token) -> dict:
    return jwt.decode(token,
                      jwt_settings.jwt_secret,
                      options={
                          "require_sub": True,
                          "require_iss": True,
                          "require_iat": True,
                          "require_exp": True
                      },
                      algorithms=[jwt_settings.jwt_algorithm],
                      issuer=jwt_settings.jwt_issuer)

def get_user_from_token(token: str) -> User:
    return get_user_from_token_info(decode_token(token))

def get_user_from_token_info(token_info: dict) -> User:
    try:
        result = db.execute(select(User).where(User.user_id == token_info["sub"].split(".")[0]))
        return result.scalars().one()
    except:
        raise

def get_user_from_user_id(user_id: str) -> User:
    try:
        result = db.execute(select(User).where(User.user_id == user_id))
        return result.scalars().one()
    except:
        raise

def get_user_from_username(username: str, raise_error: bool = True) -> User | None:
    try:
        result = db.execute(select(User).where(User.username == username))
        return result.scalars().one()
    except:
        if raise_error:
            raise
        else:
            return None

def create_db_and_tables(engine: Engine):
    misc.Base.metadata.create_all(engine)