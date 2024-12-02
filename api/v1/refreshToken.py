from classes.user import get_user_from_token_info


async def search(token_info):
    user = get_user_from_token_info(token_info)
    return user.generate_token(token_info["sub"].split(".")[1])