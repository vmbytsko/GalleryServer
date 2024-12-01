from pathlib import Path

import uvicorn
from connexion import AsyncApp, RestyResolver

from config import get_config

config = get_config()

app = AsyncApp(__name__)

app.add_api('api/v1/openapi.yaml', base_path='/api/v1', resolver=RestyResolver("api.v1"))

Path(config.data_directory).mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
