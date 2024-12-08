import uuid
from multiprocessing import Queue


class MPSQLiteAlreadyCreatedCursorRequest:
    def __init__(self, request_id, cursor_id, args, kwargs):
        self.request_id = request_id
        self.cursor_id = cursor_id
        self.args = args
        self.kwargs = kwargs

class MPSQLiteAlreadyCreatedCursorResponse:
    def __init__(self, request_id, result):
        self.request_id = request_id
        self.result = result

class MPSQLiteAlreadyCreatedCursorAttributesProxy:
    def __init__(self, already_created_cursor_id, already_created_cursor_request_queue, already_created_cursor_response_queue):
        self.__already_created_cursor_id = already_created_cursor_id
        self.__already_created_cursor_request_queue: Queue = already_created_cursor_request_queue
        self.__already_created_cursor_response_queue: Queue = already_created_cursor_response_queue

    def __call__(self, *args, **kwargs):
        request_id = str(uuid.uuid4())
        self.__already_created_cursor_request_queue.put(MPSQLiteAlreadyCreatedCursorRequest(request_id, self.__already_created_cursor_id, args, kwargs))
        while True:
            try:
                response: MPSQLiteAlreadyCreatedCursorResponse = self.__already_created_cursor_response_queue.get()

                if response.request_id != request_id:
                    self.__already_created_cursor_response_queue.put(response)
                    continue

                if issubclass(type(response.result), Exception):
                    raise response.result

                return response.result
            except:
                return None

class MPSQLiteAlreadyCreatedCursorWrapper:
    def __init__(self, already_created_cursor_id, already_created_cursor_request_queue, already_created_cursor_response_queue):
        self.__already_created_cursor_id = already_created_cursor_id
        self.__already_created_cursor_request_queue = already_created_cursor_request_queue
        self.__already_created_cursor_response_queue = already_created_cursor_response_queue

    def close(self):
        return self.__getattr__("close")()

    def __getattr__(self, name):
        return MPSQLiteAlreadyCreatedCursorAttributesProxy(self.__already_created_cursor_id, self.__already_created_cursor_request_queue, self.__already_created_cursor_response_queue)