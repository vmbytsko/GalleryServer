from classes.user import get_user_from_token_info, user_db_session_maker


async def search(token_info) -> str:
    async with user_db_session_maker() as session:
        return """
        You are username {user} and the secret is 'wbevuec'.
        Decoded token claims: {token_info}.
        """.format(
            user=(await get_user_from_token_info(session, token_info)).username, token_info=token_info
        )