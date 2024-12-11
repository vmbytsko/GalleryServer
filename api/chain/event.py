import json
import uuid
from pathlib import Path

import misc
from classes.user import get_user_from_token_info
from config import get_config

spec_paths = {
    "v1.0": {
        "/chain/{chain_name}/event": {
            "post": {
                "summary": "Add new event",
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
                "requestBody": {
                    "x-body-name": "event",
                    "description": "Event",
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object"
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Added new event",
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
        },
        "/chain/{chain_name}/event/{event_id}": {
            "get": {
                "summary": "Get event data",
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
                    },
                    {
                        "name": "event_id",
                        "description": "Event ID",
                        "in": "path",
                        "required": True,
                        "schema": {
                            "type": "string"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Event info",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object"
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Bad request",
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


def get_v1dot0(token_info: dict, chain_name: str, event_id: str):
    if not misc.check_chain_name(chain_name):
        return {
            "error": {
                "code": 1,  # TODO: create code
                "name": "malformed_chain_name",
                "description": "As a part of specification, chain name should be lowercase alpha string (only letters) with maximum length of 32."
            }
        }, 400

    if not misc.check_uuid(event_id):
        return {
            "error": {
                "code": 1,  # TODO: create code
                "name": "malformed_event_id",
                "description": "As a part of specification, Event ID should be UUID."
            }
        }, 400

    user = get_user_from_token_info(token_info)
    Path(get_config().data_directory + "/userevents/v1/" + user.user_id + "/v1/" + chain_name).mkdir(
        parents=True, exist_ok=True)
    if not Path(
            get_config().data_directory + "/userevents/v1/" + user.user_id + "/v1/" + chain_name + "/" + event_id).is_file():
        return {
            "error": {
                "code": 1,  # TODO: create own status
                "name": "not_found",
                "description": "No event with this id was found."
            }
        }, 400
    return {
        "response": {
            "event": json.loads(open(
                get_config().data_directory + "/userevents/v1/" + user.user_id + "/v1/" + chain_name + "/" + event_id,
                "r").read())
        }
    }, 200


def post_v1dot0(token_info: dict, chain_name: str, event: dict):
    if not misc.check_chain_name(chain_name):
        return {
            "error": {
                "code": 1,  # TODO: create code
                "name": "malformed_chain_name",
                "description": "As a part of specification, chain name should be lowercase alpha string (only letters) with maximum length of 32."
            }
        }, 400

    if event.get("request_id", None) is None:
        return {
            "error": {
                "code": 1,  # TODO: create code
                "name": "no_request_id",
                "description": "As a part of specification, the body of POST request must have 'request_id' parameter."
            }
        }, 400

    if not misc.check_uuid(event["request_id"]):
        return {
            "error": {
                "code": 1,  # TODO: create code
                "name": "malformed_request_id",
                "description": "As a part of specification, the 'request_id' parameter must be UUID."
            }
        }, 400

    # TODO: handle request_id: when user sends event with request_id,
    #  which was already handled in the last 24 hours,
    #  return server-generated event_id and even ignore non-matching last event
    #  and contents of the event.

    user = get_user_from_token_info(token_info)

    if user.get_last_event_id(chain_name) != event.get("parent", None):
        return {
            "error": {
                "code": 1,  # TODO: create code
                "name": "parent_mismatch",
                "description": "Event's parent event is not the last event of this chain."
            }
        }, 400

    if event.get("type", None) is None:
        return {
            "error": {
                "code": 1,  # TODO: create code
                "name": "no_event_type",
                "description": "As a part of specification, all events have to have a type."
            }
        }, 400

    if event.get("data", None) is None:
        return {
            "error": {
                "code": 1,  # TODO: create code
                "name": "no_event_data",
                "description": "As a part of specification, all events have to have 'data' key. It can be empty (no key-value pairs) (it's up to overlying application specification), but it still have to be present."
            }
        }, 400

    if event.get("v", None) is None:
        return {
            "error": {
                "code": 1,  # TODO: create code
                "name": "no_event_version",
                "description": "As a part of specification, all event have to have 'v' key, which stands for event version. This version is up to overlying application specification, but it still have to be present."
            }
        }, 400

    if not((type(event["v"]) is str) or (type(event["v"]) is int)):
        return {
            "error": {
                "code": 1,  # TODO: create code
                "name": "event_version_is_not_a_string",
                "description": "As a part of specification, version of event have to be string or integer."
            }
        }, 400

    temp_id = str(uuid.uuid4())
    misc.add_event_requests_queue.put(misc.AddEventRequest(temp_id, user.user_id, chain_name, event))
    while True:
        try:
            response: misc.AddEventResponse = misc.add_event_responses_queue.get()

            if response.temp_id != temp_id:
                misc.add_event_responses_queue.put(response)
                continue

            return {
                "response": {
                    "event_id": response.event_id
                }
            }, 200
        except:
            return {
                "error": {
                    "code": 1,  # TODO: create code
                    "name": "server_error",
                    "description": "Server could not add event to the chain. Please retry."
                }
            }, 500
