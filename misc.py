import time
from typing import Self

from sqlalchemy import TypeDecorator, Integer
from sqlalchemy.orm import declarative_base


def current_timestamp() -> int:
    return int(time.time())


Base = declarative_base()


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