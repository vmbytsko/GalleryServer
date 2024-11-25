from argparse import ArgumentParser

import yaml

__config_in_memory = None

def load_config() -> dict:
    global __config_in_memory
    if __config_in_memory is not None:
        return __config_in_memory

    __parser = ArgumentParser()

    __parser.add_argument("-c", "--config", dest="config",
                          help="Load config", metavar="FILE")

    __args = __parser.parse_args()

    __yaml_config = yaml.safe_load(open(__args.config))

    __config_in_memory = {"working_directory": __yaml_config["v1"]["working-directory"]}
    return __config_in_memory