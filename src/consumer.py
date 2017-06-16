import os
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils
from street_segment_index import StreetSegmentIndex
from feed_events import LocationEvent
from itertools import groupby
import json

from config import settings

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
        return event.car_id, [(event, subsegment)]

    def combine_events(events1, events2):
        return events1 + events2

    def expire_old_events(events, expired):
        expired_set = set(event.ts for event, _ in expired)

        return filter(lambda (event, _): event.ts not in expired_set, events)

    def group_by_cnn(items):
        def get_cnn((event, subsegment)):
            return subsegment.obj.cnn

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


    kafka_stream = create_stream(streaming_context)
    kafka_stream.flatMap(lookup_segment, preservesPartitioning=True)            \
                .map(rekey_by_car_id, preservesPartitioning=True)               \
                .reduceByKeyAndWindow(combine_events, expire_old_events,
                                      windowDuration=120, slideDuration=30,
                                      numPartitions=1)                          \
                .mapValues(group_by_cnn)                                        \
                .mapValues(drop_short_cnn_groups)                               \
                .filter(has_cnn_groups)                                         \
                .mapValues(drop_intermediary_events).pprint()

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
