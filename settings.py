import os.path

EDGE_PATH = "./street_data/street_segments.pickle"
NODE_NEIGHBORS_PATH = "./street_data/node_neighbors.json"
DB_URL = 'bolt://localhost'
USER_NAME = ""
USER_PASSWORD = ""

if os.path.exists("./settings_local.py"):
    from settings_local import *
