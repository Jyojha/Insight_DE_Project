import os.path

EDGE_PATH = "./street_data/street_segments.pickle"
NODE_NEIGHBORS_PATH = "./street_data/node_neighbors.json"
DB_URL = 'bolt://localhost'
USER_NAME = ""
USER_PASSWORD = ""

try:
	from config.settings_local import *
except ImportError:
	pass