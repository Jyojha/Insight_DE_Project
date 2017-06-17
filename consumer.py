import os
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from street_segment_index import PickleHack
from feed_events import LocationEvent
from itertools import groupby
import json

from config import settings

def group_by_car(events):
    def key(item):
        event, street = item
        return event.car_id

    grouped = []
    for car_id, group in groupby(sorted(events, key=key), key):
        grouped.append((car_id, list(group)))

    return grouped

def pred(item):
    _, events = item

    for car_id, car_events in events:
        if len(car_events) > 1:
            return True

    return False

def create_pipeline(sc, ssc):
    ssi = sc.broadcast(PickleHack())

    #Define kafka consumer
    kafka_stream = \
                   KafkaUtils.createStream(ssc,
                                           settings.ZOOKEEPER_URL,
                                           settings.KAFKA_GROUP,
                                           {settings.KAFKA_TOPIC: settings.KAFKA_TOPIC_THREADS},
                                           valueDecoder=LocationEvent.deserialize)

    with_street_names = kafka_stream.map(lambda (key, event): (event, ssi.value.index.nearest_segments(event.lon, event.lat)))
    with_street_names = with_street_names.filter(lambda (event, streets): streets)
    with_street_names = with_street_names.map(lambda (event, streets): (event, streets[0]))

    cnn_indexed = with_street_names.map(lambda (event, (radius, cnn, street)): (cnn, (event, street)))
    grouped_by_cnn = cnn_indexed.groupByKey().mapValues(lambda events: events)
    grouped_by_cnn_and_car = grouped_by_cnn.mapValues(group_by_car).filter(pred)
    windowed = grouped_by_cnn_and_car.window(120, 30)

    windowed.pprint()

def create_context():
    sc = SparkContext(appName=settings.SPARK_APP_NAME)
    sc.setLogLevel("DEBUG")
    ssc = StreamingContext(sc, 10)

    create_pipeline(sc, ssc)

    return ssc


if __name__ == '__main__':
    ssc = create_context()
    ssc.start()
    ssc.awaitTermination()
