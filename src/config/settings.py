import logging
from os import path, environ

SPARK_APP_NAME='traffic-processing'

DB_URL = 'bolt://localhost'
USER_NAME = ""
USER_PASSWORD = ""

KAFKA_URL='localhost:9092'
KAFKA_TOPIC='traffic-events'

SEGMENTS_PATH = "data/street_segments.pickle"
STREET_INDEX_PICKLE = 'data/street_segment_index.pickle'
SPEED_LIMITS_PATH = "data/speeds.json"

LOGGING_LEVEL = logging.DEBUG

SHORTEST_PATH_ALGO='dijkstra'   # dijkstra or aStar

SETTINGS_MODULE=environ.get('TRAFFIC_SETTINGS_MODULE')
if SETTINGS_MODULE is not None and SETTINGS_MODULE:
    exec("from config.settings_%s import *" % SETTINGS_MODULE)

try:
    from config.settings_local import *
except ImportError:
    pass
