import misc
from classes.user import get_user_from_token_info

spec_paths = {
    "v1.0": {
        "/chain/{chain_name}/last": {
            "get": {
                "summary": "Get last event id of this chain",
                "security": [
                    {
                        "jwt": ["secret"]
                    }
                ],
                "parameters": [
                    {
                        "name": "chain_name",
                        "description": "Chain name",
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Getting last event id success",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


def search_v1dot0(token_info: dict, chain_name: str):
    if not misc.check_chain_name(chain_name):
        return {
            "error": {
                "code": 1,  # TODO: create code
                "name": "malformed_chain_name",
                "description": "As a part of specification, chain name should be lowercase alpha string (only letters) with maximum length of 32."
            }
        }, 400

    user = get_user_from_token_info(token_info)
    last_event_id = user.get_last_event_id(chain_name)
    if last_event_id is None:
        return {
            "error": {
                "code": 1,  # TODO: create own status
                "name": "not_found",
                "description": "This chain doesn't have any events."
            }
        }, 400
    return {
        "response": {
            "last": last_event_id
        }
    }

# no post/put as there will be no force push