from kafka import KafkaProducer
from kafka.partitioner.roundrobin import RoundRobinPartitioner
from kafka.errors import KafkaError
import json

from car_events_pb2 import CarId, CarEvent


class LocationEvent(object):
    def __init__(self, car_id, lat, lon, timestamp):
        self.car_id = car_id
        self.lat = lat
        self.lon = lon
        self.timestamp = timestamp

    def get_key(self):
        pb_key = CarId()
        pb_key.id = self.car_id
        return pb_key.SerializeToString()

    def serialize(self):
        pb_event = CarEvent()
        pb_event.id = self.car_id
        pb_event.lat = self.lat
        pb_event.lon = self.lon
        pb_event.timestamp = self.timestamp

        return pb_event.SerializeToString()

    def deserialize(self, data):
        pb_event = CarEvent()
        pb_event.ParseFromString(data)

        self.car_id = pb_event.id
        self.lat = pb_event.lat
        self.lon = pb_event.lon
        self.timestamp = pb_event.timestamp


producer = KafkaProducer(bootstrap_servers=['localhost:9092'], 
    value_serializer=LocationEvent.serialize, partitioner=RoundRobinPartitioner())
topic = "ingestiontest"

test_data = LocationEvent(1, 37, 122, 123456)

for i in range(50000):
    producer.send(topic, test_data, test_data.get_key())
