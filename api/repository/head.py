from classes.user import get_user_from_token_info

spec_paths = {
    "v1.0": {
        "/repository/{repository_name}/head": {
            "get": {
                "summary": "Get head of this repository",
                "security": [
                    {
                        "jwt": ["secret"]
                    }
                ],
                "parameters": [
                    {
                        "name": "repository_name",
                        "description": "Repository name",
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Getting head success",
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


def search_v1dot0(token_info: dict, repository_name: str):
    user = get_user_from_token_info(token_info)
    head = user.get_head(repository_name)
    if head is None:
        return {
            "error": {
                "code": 1,  # TODO: create own status
                "name": "not_found",
                "description": "This repository has not been initiated yet because of no HEAD file."
            }
        }, 400
    return {
        "response": {
            "head": head
        }
    }

# no post/put as there will be no force push