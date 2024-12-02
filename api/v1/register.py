import uuid

from classes.user import User, UserStatus


async def search(username: str, password: str):
    user = User(str(uuid.uuid4()), new=True)

    user.status = UserStatus.ACTIVE
    user.username = username
    user.password = password

    user.save(new=True)
    return user.generate_token()