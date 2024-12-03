from classes.user import get_user_from_token_info, user_db_session_maker


async def search(token_info):
    async with user_db_session_maker() as session:
        user = await get_user_from_token_info(session, token_info)
        return user.generate_token(token_info["sub"].split(".")[1])