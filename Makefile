all: car_events_pb2.py

# left side (car_events_pb2.py) -- the goal
# right side (protobuf/car_events.proto) -- dependencies
#
# whenever the goal's timestamp is older than the timestamp of any 
# of the dependencies, the specified commands are used to regenerate 
# the goal
car_events_pb2.py: protobuf/car_events.proto
	protoc --proto_path=protobuf/ --python_out=./ $<
