import os
import operator

from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from street_segment_index import StreetSegmentIndex
from feed_events import LocationEvent
from itertools import groupby
import json

from config import settings
from distance import StreetInfoIndex

from neo4j_utils import update_times

def create_stream(streaming_context):
    topics = [settings.KAFKA_TOPIC]
    config = {"bootstrap.servers": settings.KAFKA_URL}

    return KafkaUtils.createDirectStream(streaming_context, topics, config,
                                         valueDecoder=LocationEvent.deserialize)

def create_pipeline(context, streaming_context):
    street_index = context.broadcast(StreetSegmentIndex.read_pickle())
    def lookup_segment((key, event)):
        index = street_index.value

        return [(event, subsegment)
                for _, _, subsegment in index.nearest_segments(lat=event.lat,
                                                               lon=event.lon,
                                                               num=1)]

    def rekey_by_car_id((event, subsegment)):
        return event.car_id, (event, subsegment)

    def combine_events(partition):
        def get_id(item):
            return item[0]

        for car_id, group in groupby(sorted(partition, key=get_id), get_id):
            yield car_id, [event for _, event in group]

    def recombine_events(partition):
        def get_id(item):
            return item[0]

        for car_id, group in groupby(sorted(partition, key=get_id), get_id):
            yield car_id, reduce(operator.add,
                                 (events for _, events in group))

    def group_by_cnn(items):
        def get_cnn((event, subsegment)):
            return subsegment.cnn

        for cnn, group in groupby(sorted(items, key=get_cnn), get_cnn):
            yield cnn, list(group)

    def drop_short_cnn_groups(groups):
        return filter(lambda (_, events): len(events) > 1, groups)

    def has_cnn_groups((car_id, groups)):
        return bool(groups)

    def drop_intermediary_events(groups):
        def get_timestamp((event, _)):
            return event.timestamp

        result = []
        for cnn, events in groups:
            start_event = min(events, key=get_timestamp)
            end_event   = max(events, key=get_timestamp)

            result.append( (cnn, (start_event, end_event)) )

        return result

    def drop_car_id( (car, cnn_groups) ):
        return cnn_groups

    street_info_index = context.broadcast(StreetInfoIndex())
    def find_distance_and_time((cnn, (start_event, end_event))):
        index = street_info_index.value

        start_ts = start_event[0].timestamp
        end_ts   = end_event[0].timestamp

        time_taken = end_ts - start_ts

        info = index.get_info(cnn)
        distance, direction = index.get_movement_info(start_event, end_event)

        return ((cnn, direction), (distance, time_taken))

    def drop_unknown_direction( ((cnn, direction), (distance, time_taken)) ):
        return direction is not None

    def sum_distance_and_time( (d1, t1), (d2, t2) ):
        return (d1 + d2, t1 + t2)

    def compute_expected_time_and_speed( (street, (totalDistance, totalTime)) ):
        cnn, direction = street

        info = street_info_index.value.get_info(cnn)
        length = info.length

        try:
            avg_speed = totalDistance / totalTime
            expected_time = length / avg_speed
        except ZeroDivisionError:
            # Just assume that things are very slow. Ten meters per minute
            # seems slow enough.
            avg_speed = 10 / 60.
            expected_time = length / avg_speed

        street_info = street_info_index.value.get_info(cnn)

        return (street_info, direction, expected_time, avg_speed)

    kafka_stream = create_stream(streaming_context)
    kafka_stream.flatMap(lookup_segment, preservesPartitioning=True)            \
                .map(rekey_by_car_id, preservesPartitioning=True)               \
                .mapPartitions(combine_events, preservesPartitioning=True)      \
                .window(windowDuration=120, slideDuration=30)                   \
                .mapPartitions(recombine_events, preservesPartitioning=True)    \
                .mapValues(group_by_cnn)                                        \
                .mapValues(drop_short_cnn_groups)                               \
                .filter(has_cnn_groups)                                         \
                .mapValues(drop_intermediary_events)                            \
                .flatMap(drop_car_id, preservesPartitioning=True)               \
                .map(find_distance_and_time, preservesPartitioning=True)        \
                .filter(drop_unknown_direction)                                 \
                .reduceByKey(sum_distance_and_time)                             \
                .map(compute_expected_time_and_speed,
                     preservesPartitioning=True)                                \
                .repartition(1).foreachRDD(lambda rdd: update_times(rdd.collect()))

def create_context():
    context = SparkContext(appName=settings.SPARK_APP_NAME)
    context.setLogLevel("WARN")

    streaming_context = StreamingContext(context, 10)
    create_pipeline(context, streaming_context)

    streaming_context.checkpoint("/tmp/checkpoint")
    return streaming_context

if __name__ == '__main__':
    streaming_context = create_context()
    streaming_context.start()
    streaming_context.awaitTermination()
