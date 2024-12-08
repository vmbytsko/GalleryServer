from classes.user import get_user_from_username

spec_paths = {
    "v1.0": {
        "/auth/login": {
            "get": {
                "summary": "Return JWT token",
                "parameters": [
                    {
                        "name": "username",
                        "description": "Username",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "password",
                        "description": "User password",
                        "in": "query",
                        "required": True,
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "JWT token",
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


def search_v1dot0(username: str, password: str):
    user = get_user_from_username(username)
    if user.password != password:
        raise Exception
    return {
        "response": {
            "token": user.generate_token()
        }
    }, 200
