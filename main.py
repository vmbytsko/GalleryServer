import multiprocessing
import threading
from pathlib import Path

from connexion import AsyncApp
from sqlalchemy import create_engine
from sqlalchemy.dialects import registry
from sqlalchemy.orm import sessionmaker

import misc
from classes import user
from classes.user import get_user_from_user_id
from config import get_config
from misc import StandaloneApplication, API_VERSIONS

config = get_config()

def __worker_thread():
    while True:
        try:
            request: misc.CommitRequest = misc.commit_requests_queue.get()
            user = get_user_from_user_id(request.user_id)
            commit_id = user.add_commit(request.repository_name, request.commit)
            queue_item_result = misc.CommitResponse(request.temp_id, 0, commit_id)
            misc.commit_responses_queue.put(queue_item_result)
        except:
            continue

if __name__ != "__main__":
    app = AsyncApp(__name__)
    for version in API_VERSIONS:
        app.add_api(f'openapis/openapi_{version}.yaml', base_path=f'/api/{version}', resolver=misc.CustomRestyResolver(version))
    app.add_api(f'openapis/openapi_nonversioned.yaml', base_path=f'/api', resolver=misc.CustomRestyResolver("nonversioned"))

if __name__ == "__main__":
    misc.generate_versioned_openapis()

    Path(config.data_directory).mkdir(parents=True, exist_ok=True)

    registry.register("sqlite.mpsqlite", "mpsqlite.main", "MPSQLiteDialect")
    __user_db_engine = create_engine(
        "sqlite+mpsqlite:///" + get_config().data_directory + "/db/users.db")

    user_db_session_maker = sessionmaker(__user_db_engine, expire_on_commit=False)  # TODO: remove expire_on_commit
    user.create_db_and_tables(__user_db_engine)
    with user_db_session_maker() as session:
        user.db = session

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
