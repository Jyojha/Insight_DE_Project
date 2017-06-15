import logging
from os import path, environ

SPARK_APP_NAME='traffic-processing'

SEGMENTS_PATH = "data/street_segments.pickle"
DB_URL = 'bolt://localhost'
USER_NAME = ""
USER_PASSWORD = ""

KAFKA_URL='localhost:9092'
KAFKA_TOPIC='traffic-events'

STREET_INDEX_PICKLE = 'data/street_segment_index.pickle'

LOGGING_LEVEL = logging.DEBUG

SETTINGS_MODULE=environ.get('TRAFFIC_SETTINGS_MODULE')
if SETTINGS_MODULE is not None:
    exec("from config.settings_%s import *" % SETTINGS_MODULE)

try:
    from config.settings_local import *
except ImportError:
    pass
