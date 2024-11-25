from argparse import ArgumentParser

import yaml


def load_config() -> dict:
    __parser = ArgumentParser()

    __parser.add_argument("-c", "--config", dest="config",
                          help="Load config", metavar="FILE")

    __args = __parser.parse_args()

    __yaml_config = yaml.safe_load(open(__args.config))

    config = {"working_directory": __yaml_config["v1"]["working-directory"]}
    return config