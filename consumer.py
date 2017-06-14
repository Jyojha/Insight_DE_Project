import os
#os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-streaming-kafka-0-8_2.11:2.0.2'
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from street_segment_index import PickleHack
from feed_events import LocationEvent
from itertools import groupby
import json

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
    kafka_stream = KafkaUtils.createStream(ssc, 'localhost:2181', 'spark-streaming-01', {'events4':1},
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
    sc = SparkContext(appName="PythonSparkStreamingKafka_RM_02")
    sc.setLogLevel("WARN")
    ssc = StreamingContext(sc, 10)

    create_pipeline(sc, ssc)

    #Processing
    #Extract geocoords
    #parsed = kafka_stream.map(lambda ev: (ev.lat, ev.lon))

    #Count number of geocoords in this batch
    #count_this_batch = kafka_stream.count().map(lambda x: ('Geocoords this batch: %s' %x))

    #Count by windowed time period
    #count_windowed_events = kafka_stream.countByWindow(10, 10).map(lambda x: "Number of events: %s" % x).pprint()

    return ssc


ssc = StreamingContext.getOrCreate('/tmp/checkpoint_v01', create_context)
ssc.start()
ssc.awaitTermination()
