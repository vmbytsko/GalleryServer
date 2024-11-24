import starlette.datastructures


async def post(file):
    assert isinstance(file, starlette.datastructures.UploadFile)
    return f"Hello", 200