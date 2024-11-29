from argparse import ArgumentParser
from enum import Enum

import yaml


class Config:
    class Authentication:
        class Types(Enum):
            builtin = "builtin"

        auth_type: Types

    data_directory: str
    authentication: Authentication


__config_in_memory: Config = None


def get_config() -> Config:
    global __config_in_memory
    if __config_in_memory is not None:
        return __config_in_memory

    __parser = ArgumentParser()
    __parser.add_argument("-c", "--config", dest="config", metavar="FILE")
    __args = __parser.parse_args()

    __actual_version = __update_config()
    __yaml_config = yaml.safe_load(open(__args.config))

    __temp_config = Config()
    __temp_config.data_directory = __yaml_config[__actual_version]["dataDirectory"]
    __temp_config.authentication = Config.Authentication()
    __temp_config.authentication.auth_type = Config.Authentication.Types(__yaml_config["v1"]["authentication"]["type"])

    __config_in_memory = __temp_config
    return __config_in_memory

def __update_config() -> str:
    # every time config parameters are updated and they need to be rewrited, new version appears
    return "v1"
