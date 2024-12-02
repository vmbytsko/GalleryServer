from classes.user import get_user_from_token_info


def search(token_info):
    user = get_user_from_token_info(token_info)
    head = user.get_head()
    if head is None:
        return None, 404
    return head

# no put as there will be no force push