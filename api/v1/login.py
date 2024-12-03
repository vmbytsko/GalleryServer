from classes.user import get_user_from_username, user_db_session_maker


async def search(username: str, password: str):
    async with user_db_session_maker() as session:
        user = await get_user_from_username(session, username)
        if user.password != password:
            raise Exception
        return user.generate_token()