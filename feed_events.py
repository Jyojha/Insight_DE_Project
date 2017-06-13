from kafka import KafkaProducer
from kafka.partitioner.roundrobin import RoundRobinPartitioner
from kafka.errors import KafkaError
import json
from os.path import basename, join
from datetime import datetime, timedelta
import time
import math
from glob import glob

from car_events_pb2 import CarId, CarEvent

START_WINDOW = datetime(2008, 6, 6, 8, 00, 00)
STOP_WINDOW = START_WINDOW + timedelta(minutes=60)
START_WINDOW_TS = math.trunc(time.mktime(START_WINDOW.timetuple()))
STOP_WINDOW_TS = math.trunc(time.mktime(STOP_WINDOW.timetuple()))

class LocationEvent(object):
    def __init__(self, car_id, lat, lon, occupied, timestamp):
        self.car_id = car_id
        self.lat = lat
        self.lon = lon
        self.occupied = occupied
        self.timestamp = timestamp

    def __repr__(self):
        return 'LocationEvent("%s", %f, %f, %s, %d)' % (self.car_id, self.lat, self.lon,
                                                        self.occupied, self.timestamp)

    def get_key(self):
        pb_key = CarId()
        pb_key.id = self.car_id
        return pb_key.SerializeToString()

    def serialize(self):
        pb_event = CarEvent()
        pb_event.id = self.car_id
        pb_event.lat = self.lat
        pb_event.lon = self.lon
        pb_event.occupied = self.occupied
        pb_event.timestamp = self.timestamp

        return pb_event.SerializeToString()

    @classmethod
    def deserialize(cls, data):
        pb_event = CarEvent()
        pb_event.ParseFromString(data)

        car_id = pb_event.id
        lat = pb_event.lat
        lon = pb_event.lon
        occupied = pb_event.occupied
        timestamp = pb_event.timestamp

        return cls(car_id, lat, lon, occupied, timestamp)

def read_file(path):
    base_name = basename(path)
    components = base_name.split('.')

    if len(components) > 1:
        car_id = '.'.join(components[:-1])
    else:
        car_id = components[0]

    with open(path, "r") as f:
        for line in f:
            line = line.strip().split(" ")
            lat = float(line[0])
            lon = float(line[1])
            occupied = bool(int(line[2]))
            timestamp = int(line[3])

            yield LocationEvent(car_id, lat, lon, occupied, timestamp)

def filter_events(start_window_ts, stop_window_ts, events):
    for event in events:
        if event.timestamp > stop_window_ts:
            return
        if start_window_ts <= event.timestamp <= stop_window_ts:
            yield event

# read all the cab data files from the directory and extract the events for the specified window
def read_directory(start_window_ts, stop_window_ts, directory):
    files = glob(join(directory, "*.txt"))
    all_events = []
    for file in files:
        events = filter_events(start_window_ts, stop_window_ts, read_file(file))
        all_events.extend(events)

    all_events.sort(key=lambda ev: ev.timestamp)

    return all_events

def create_kafka_producer(bootstrap_servers=['localhost:9092']):
    producer = KafkaProducer(bootstrap_servers=bootstrap_servers,
                             value_serializer=LocationEvent.serialize)

    return producer

def replay_events(all_events, topic_name='events3'):
    producer = create_kafka_producer()
    topic = topic_name

    for event in all_events:
        producer.send(topic, event, event.get_key())

if __name__ == '__main__':
    print "Reading events"
    events = read_directory(START_WINDOW_TS, STOP_WINDOW_TS, "./cabspottingdata")
    print "Number of events to replay: %d" % len(events)
    print "Replaying the events"
    replay_events(events)
