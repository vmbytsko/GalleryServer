from classes.user import get_user_from_token_info


def search(token_info) -> str:
    return """
    You are user_id {user} and the secret is 'wbevuec'.
    Decoded token claims: {token_info}.
    """.format(
        user=get_user_from_token_info(token_info).username, token_info=token_info
    )