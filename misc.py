import importlib
import os
import time
import uuid
from asyncio import iscoroutinefunction, iscoroutine
from multiprocessing import Queue
from pathlib import Path
from types import coroutine
from typing import Self

import yaml
from connexion import RestyResolver
from gunicorn.app.wsgiapp import WSGIApplication
from sqlalchemy import TypeDecorator, Integer
from sqlalchemy.orm import declarative_base, DeclarativeBase


API_VERSIONS = ["v1.4", "v1.3", "v1.2", "v1.1", "v1.0"]

def current_timestamp() -> int:
    return int(time.time())


Base: DeclarativeBase = declarative_base()


class IntEnum(TypeDecorator):
    """
    Enables passing in a Python enum and storing the enum's *value* in the db.
    The default would have stored the enum's *name* (ie the string).

    https://gist.github.com/hasansezertasan/691a7ef67cc79ea669ff76d168503235
    """

    impl = Integer

    def __init__(self, enumtype, *args, **kwargs):
        super(IntEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value: Self, dialect):
        if isinstance(value, int):
            return value

        return value.value

    def process_result_value(self, value, dialect):
        return self._enumtype(value)

class StandaloneApplication(WSGIApplication):
    def __init__(self, app_uri, options=None):
        self.options = options or {}
        self.app_uri = app_uri
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.app_uri


commit_requests_queue: Queue
commit_responses_queue: Queue


class CommitRequest:
    def __init__(self, temp_id: str, user_id: str, repository_name: str, commit: dict):
        self.temp_id = temp_id
        self.user_id = user_id
        self.repository_name = repository_name
        self.commit = commit

class CommitResponse:
    def __init__(self, temp_id: str, result: int, commit_id: str):
        self.temp_id = temp_id
        self.result = result
        self.commit_id = commit_id


def handle_incoming_commit(user, repository_name, commit):
    temp_id = str(uuid.uuid4())
    commit_requests_queue.put(CommitRequest(temp_id, user.user_id, repository_name, commit))
    while True:
        try:
            response: CommitResponse = commit_responses_queue.get()

            if response.temp_id != temp_id:
                commit_responses_queue.put(response)
                continue

            return response.commit_id
        except:
            return None


ERROR_RESPONSE = {
        "error": {
            "code": 1,  # TODO: create own status
            "name": "unknown_api_version",
            "description": "Specified API version is unknown to the server. "
                           "Maybe it is too old or very new, so you should "
                           "either update your application or ask "
                           "administrator to update the server."
        }
    }, 400, {"Content-Type": "application/json"}

async def async_versioned(func, version: str, max_version: str = None, allow_no_version: bool = False, *args, **kwargs):
    result = versioned(func, version, max_version, allow_no_version, *args, **kwargs)
    if iscoroutine(result):
        return await result
    else:
        return result

def versioned(func, version: str = None, max_version: str = None, allow_no_version: bool = False, *args, **kwargs):
    def wrap(versioned_function_string):
        try:
            return getattr(func, versioned_function_string)(*args, **kwargs)
        except TypeError as e:
            message = str(e)
            if "got an unexpected keyword argument" in message:
                unexpected_arg = message.split("'")[1]
                kwargs.pop(unexpected_arg, None)
                return wrap(versioned_function_string)
            else:
                raise

    if version is None:
        if allow_no_version:
            return wrap("nonversioned")
        else:
            return ERROR_RESPONSE

    if version not in API_VERSIONS:
        return ERROR_RESPONSE

    if max_version is not None:
        if API_VERSIONS.index(version) < API_VERSIONS.index(max_version):
            return ERROR_RESPONSE

    api_versions_known_to_client = API_VERSIONS[API_VERSIONS.index(version):]

    for i in api_versions_known_to_client:
        versioned_function_string = f"{i.replace(".", "dot")}"
        try:
            return wrap(versioned_function_string)
        except AttributeError as e:
            if versioned_function_string not in str(e):
                raise

    return ERROR_RESPONSE

def generate_versioned_openapis():
    api_versions_with_unversioned = API_VERSIONS.copy()
    api_versions_with_unversioned.append("nonversioned")
    versioned_spec_paths = {k: {} for k in api_versions_with_unversioned}

    for subdir, dirs, files in os.walk("api"):
        for file in files:
            if file.endswith(".py"):
                file_spec_paths = getattr(importlib.import_module(f"{subdir.replace("/", ".")}.{file[:-3]}"),
                                          "spec_paths")

                def get_spec_paths_for_this_version(version):
                    if version == "nonversioned":
                        return file_spec_paths.get("nonversioned", {})
                    for existing_version in API_VERSIONS[API_VERSIONS.index(version):]:
                        try:
                            return file_spec_paths[existing_version]
                        except:
                            pass
                    return {}

                for version in api_versions_with_unversioned:
                    spec_paths_for_this_version = get_spec_paths_for_this_version(version)
                    for k, v in spec_paths_for_this_version.items():
                        versioned_spec_paths[version][f"{k}"] = v

    Path("openapis").mkdir(parents=True, exist_ok=True)

    for version in api_versions_with_unversioned:
        with open(f'openapis/openapi_{version}.yaml', 'w+') as f:
            yaml.dump({
                "openapi": "3.0.0",
                "info": {
                    "title": "TwiceSafe Vault API",
                    "version": version,
                    "description": "API for clients"
                },
                "components": {
                    "securitySchemes": {
                        "jwt": {
                            "type": "http",
                            "scheme": "bearer",
                            "bearerFormat": "JWT",
                            "x-bearerInfoFunc": "classes.user.decode_token"
                        }
                    }
                },
                "paths": versioned_spec_paths[version]
            }, f, allow_unicode=True)

class CustomRestyResolver(RestyResolver):
    def __init__(self, version: str, *, collection_endpoint_name: str = "search"):
        """
        :param default_module_name: Default module name for operations
        :param collection_endpoint_name: Name of function to resolve collection endpoints to
        """
        super().__init__("api", collection_endpoint_name=collection_endpoint_name)
        self.version = version

    def resolve_operation_id(self, operation):
        """
        Resolves the operationId using REST semantics unless explicitly configured in the spec

        :type operation: connexion.operations.AbstractOperation
        """
        if operation.operation_id:
            return super().resolve_operation_id(operation)

        def get_versioned_function_name(version):
            if version == "nonversioned":
                return self.resolve_operation_id_using_rest_semantics(operation)+"_"+self.version.replace(".", "dot")
            for existing_version in API_VERSIONS[API_VERSIONS.index(version):]:
                modulename = ".".join(self.resolve_operation_id_using_rest_semantics(operation).split(".")[:-1])
                functionname = self.resolve_operation_id_using_rest_semantics(operation).split(".")[-1]

                module = importlib.import_module(modulename)
                if not hasattr(module, functionname+"_"+existing_version.replace(".", "dot")):
                    continue
                return self.resolve_operation_id_using_rest_semantics(operation)+"_"+existing_version.replace(".", "dot")
            return None

        return get_versioned_function_name(self.version)


