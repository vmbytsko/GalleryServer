import asyncio
import multiprocessing
import threading
from pathlib import Path

from connexion import AsyncApp, RestyResolver

import misc
from classes import user
from classes.user import user_db_session_maker, get_user_from_user_id
from config import get_config
from misc import StandaloneApplication

config = get_config()

app = AsyncApp(__name__)

app.add_api('api/v1/openapi.yaml', base_path='/api/v1', resolver=RestyResolver("api.v1"))

Path(config.data_directory).mkdir(parents=True, exist_ok=True)

def __worker_thread():
    async def async_thread():
        async with user_db_session_maker() as session:
            while True:
                try:
                    request: misc.CommitRequest = misc.commit_requests_queue.get()
                    user = await get_user_from_user_id(session, request.user_id)
                    commit_id = user.add_commit(request.repository_name, request.commit)
                    queue_item_result = misc.CommitResponse(request.temp_id, 0, commit_id)
                    misc.commit_responses_queue.put(queue_item_result)
                except:
                    continue

    asyncio.run(async_thread())


if __name__ == "__main__":
    asyncio.run(user.create_db_and_tables())

    misc.commit_requests_queue = multiprocessing.Manager().Queue()
    misc.commit_responses_queue = multiprocessing.Manager().Queue()

    t = threading.Thread(target=__worker_thread)
    t.daemon = True
    t.start()

    options = {
        "workers": (multiprocessing.cpu_count() * 2) + 1,
        "worker_class": "uvicorn.workers.UvicornWorker",
    }
    StandaloneApplication(f"{Path(__file__).stem}:app", options).run()
