import uuid

from classes.user import User, UserStatus, user_db_session_maker


async def search(username: str, password: str):
    async with user_db_session_maker() as session:
        user = User(user_id=str(uuid.uuid4()))

        user.status = UserStatus.ACTIVE
        user.username = username
        user.password = password
        await user.save(session, new=True)

        return user.generate_token()