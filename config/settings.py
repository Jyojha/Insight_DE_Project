from os import path

CONFIG_DIR = path.abspath(path.dirname(__file__))
ROOT_DIR = path.abspath(path.join(CONFIG_DIR, '..'))

SEGMENT_PATH = path.join(ROOT_DIR, "street_data/street_segments.pickle")
NODE_NEIGHBORS_PATH = path.join(ROOT_DIR, "street_data/node_neighbors.json")
DB_URL = 'bolt://localhost'
USER_NAME = ""
USER_PASSWORD = ""

try:
    from config.settings_local import *
except ImportError:
    pass
