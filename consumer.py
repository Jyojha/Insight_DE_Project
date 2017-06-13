import os
#os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-streaming-kafka-0-8_2.11:2.0.2'
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from street_segment_index import StreetSegment, StreetSegmentIndex
from feed_events import LocationEvent
import json

def create_context():
    sc = SparkContext(appName="PythonSparkStreamingKafka_RM_02")
    sc.setLogLevel("WARN")
    ssc = StreamingContext(sc, 10)

    #Define kafka consumer
    kafka_stream = KafkaUtils.createStream(ssc, 'localhost:2181', 'spark-streaming-3', {'events3':2},
                                           valueDecoder=LocationEvent.deserialize)

    #Processing
    #Extract geocoords
    parsed = kafka_stream.map(lambda ev: (ev.lat, ev.lon))

    #Count number of geocoords in this batch
    count_this_batch = kafka_stream.count().map(lambda x: ('Geocoords this batch: %s' %x))

    #Count by windowed time period
    count_windowed_events = kafka_stream.countByWindow(10, 10).map(lambda x: "Number of events: %s" % x).pprint()

    return ssc


ssc = StreamingContext.getOrCreate('/tmp/checkpoint_v04', create_context)
ssc.start()
ssc.awaitTermination()
#ssc.stop()
