from os import path

SPARK_APP_NAME='traffic-processing'

SEGMENTS_PATH = "data/street_segments.pickle"
DB_URL = 'bolt://localhost'
USER_NAME = ""
USER_PASSWORD = ""

KAFKA_URL='localhost:9092'
KAFKA_TOPIC='traffic-events'

STREET_INDEX_PICKLE = 'data/street_segment_index.pickle'

try:
    from config.settings_local import *
except ImportError:
    pass
