import time
import uuid
from multiprocessing import Queue
from typing import Self

from gunicorn.app.wsgiapp import WSGIApplication
from sqlalchemy import TypeDecorator, Integer
from sqlalchemy.orm import declarative_base, DeclarativeBase


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