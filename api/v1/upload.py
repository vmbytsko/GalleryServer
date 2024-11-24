import starlette.datastructures


def post(file):
    assert isinstance(file, starlette.datastructures.UploadFile)

    return f"Hello", 200