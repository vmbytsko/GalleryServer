import os
import uuid
from asyncio import QueueEmpty
from pathlib import Path

import misc
from classes.user import get_user_from_token_info, user_db_session_maker
from config import get_config

async def get(token_info: dict, repository_name: str, commit_id: str):
    async with user_db_session_maker() as session:
        user = await get_user_from_token_info(session, token_info)
        Path(get_config().data_directory + "/usercommits/v1/" + user.user_id + "/v1/" + repository_name).mkdir(
            parents=True, exist_ok=True)
        if not Path(
                get_config().data_directory + "/usercommits/v1/" + user.user_id + "/v1/" + repository_name + "/"+commit_id).is_file():
            return None, 404
        return open(get_config().data_directory + "/usercommits/v1/" + user.user_id + "/v1/" + repository_name + "/" + commit_id,
                    "r").read()


async def post(token_info: dict, repository_name: str, commit: dict):
    async with user_db_session_maker() as session:
        user = await get_user_from_token_info(session, token_info)
        commit_id = misc.handle_incoming_commit(user, repository_name, commit)
        return commit_id
