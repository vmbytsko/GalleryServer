from classes.user import User


def search(user, token_info) -> str:
    return """
    You are user_id {user} and the secret is 'wbevuec'.
    Decoded token claims: {token_info}.
    """.format(
        user=User(user.split(".")[0]).username, token_info=token_info
    )