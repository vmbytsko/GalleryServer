from classes.user import get_user_from_token_info, user_db_session_maker


async def search(token_info: dict, repository_name: str):
    async with user_db_session_maker() as session:
        user = await get_user_from_token_info(session, token_info)
        head = user.get_head(repository_name)
        if head is None:
            return None, 404
        return head

# no put as there will be no force push