from os import path

CONFIG_DIR = path.abspath(path.dirname(__file__))
ROOT_DIR = path.abspath(path.join(CONFIG_DIR, '..'))

SPARK_APP_NAME='traffic-processing'

SEGMENT_PATH = path.join(ROOT_DIR, "street_data/street_segments.pickle")
DB_URL = 'bolt://localhost'
USER_NAME = ""
USER_PASSWORD = ""

KAFKA_URL='localhost:9092'
KAFKA_TOPIC='traffic-events'
KAFKA_TOPIC_THREADS=1
KAFKA_GROUP='traffic-processing'

ZOOKEEPER_URL='localhost:2181'

try:
    from config.settings_local import *
except ImportError:
    pass
