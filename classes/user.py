import uuid
from pathlib import Path

from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

import misc
from config import get_config
from security import get_jwt_settings

config = get_config()
jwt_settings = get_jwt_settings()


__user_db_engine = create_async_engine("sqlite+aiosqlite:///"+get_config().data_directory+"/db/users.db", echo=True)

user_db_session_maker = sessionmaker(__user_db_engine, class_=AsyncSession)

class UserStatus(misc.IntEnum):
    DELETED_UNSPECIFIED = -1
    ACTIVE = 0

class User(misc.Base):
    __tablename__ = "UsersV1"

    user_id: Mapped[str] = mapped_column(primary_key=True)
    status: Mapped[UserStatus] = mapped_column(misc.IntEnum(UserStatus))
    username: Mapped[str]
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

    def get_head(self):
        Path(get_config().data_directory + "/usercommits/v1/" + self.user_id + "/v1").mkdir(parents=True, exist_ok=True)
        if not Path(get_config().data_directory + "/usercommits/v1/" + self.user_id + "/v1/HEAD").is_file():
            return None
        return open(get_config().data_directory + "/usercommits/v1/" + self.user_id + "/v1/HEAD", "r").read()

    async def save(self, session: AsyncSession, new: bool = False):
        try:
            if new:
                session.add(self)
            else:
                await session.merge(self)
        except:
            await session.rollback()
            raise
        else:
            await session.commit()

    def __repr__(self) -> str:
        return f"User(user_id={self.user_id})"


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

async def get_user_from_token(token: str) -> User:
    return await get_user_from_token_info(decode_token(token))

async def get_user_from_token_info(session: AsyncSession, token_info: dict) -> User:
    try:
        result = await session.execute(select(User).where(User.user_id == token_info["sub"].split(".")[0]))
        return result.scalars().one()
    except:
        raise

async def get_user_from_username(session: AsyncSession, username: str) -> User:
    try:
        result = await session.execute(select(User).where(User.username == username))
        return result.scalars().one()
    except:
        raise