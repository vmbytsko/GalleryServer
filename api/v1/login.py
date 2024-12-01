import uuid

from classes.user import get_user_from_username


async def search(username: str, password: str):
    user = get_user_from_username(username)
    return user.generate_token(str(uuid.uuid4()))