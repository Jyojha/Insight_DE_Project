all: src/car_events_pb2.py

# left side (car_events_pb2.py) -- the goal
# right side (protobuf/car_events.proto) -- dependencies
#
# whenever the goal's timestamp is older than the timestamp of any
# of the dependencies, the specified commands are used to regenerate
# the goal
src/car_events_pb2.py: src/protobuf/car_events.proto
	protoc --proto_path=src/protobuf/ --python_out=src/ $<
