all: src/car_events_pb2.py

# left side (car_events_pb2.py) -- the goal
# right side (protobuf/car_events.proto) -- dependencies
#
# whenever the goal's timestamp is older than the timestamp of any
# of the dependencies, the specified commands are used to regenerate
# the goal
src/car_events_pb2.py: src/protobuf/car_events.proto
	protoc --proto_path=src/protobuf/ --python_out=src/ $<


JOB_SOURCES = $(shell find src/config/ -type f -name *.py) \
              $(shell find src/data/ -type f)              \
              $(shell ls src/*.py)

job.zip: $(JOB_SOURCES)
	cd src/ && zip ../job.zip $(shell echo $(JOB_SOURCES) | sed -e 's,src/,,g')
