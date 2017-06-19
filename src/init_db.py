#!/usr/bin/env python2

import pandas as pd
from neo4j.v1 import GraphDatabase, basic_auth
from config import settings

from data_utils import read_segments, extract_intersections
from data_utils import read_speed_limits, post_process_segments

def main():
    '''Populate the static road network data in to the database'''

    # Define the entry point to the database
    driver = GraphDatabase.driver(settings.DB_URL,
                                  auth=basic_auth(settings.USER_NAME,
                                                  settings.USER_PASSWORD))
    db = driver.session()

    print "Dropping indexes"

    try:
        r = db.run("DROP INDEX ON :Intersection(cnn)")
        r.summary()
    except:
        # index might not exist
        pass

    try:
        r = db.run("DROP INDEX ON :Segment(cnn)")
        r.summary()
    except:
        # index might not exist
        pass

    print "Deleting everything"
    r = db.run("MATCH (n) DETACH DELETE n")
    r.summary()

    # Read the data
    segments = read_segments()
    speeds = read_speed_limits()
    nodes = extract_intersections(segments)

    processed_segments = post_process_segments(segments, speeds)

    print "Creating intersections"
    r = db.run('''UNWIND {nodes} as node
                  CREATE (n:Intersection)
                  SET n = node
               ''', nodes=nodes)
    r.summary()

    print "Creating intersections index"
    r = db.run('CREATE INDEX ON :Intersection(cnn)')
    r.summary()

    print "Creating street segments"
    r = db.run(
        '''UNWIND {segments} as segment
           MATCH (f:Intersection {cnn: segment.from_cnn}),
                 (t:Intersection {cnn: segment.to_cnn})
           CREATE (f)-[s:Segment {cnn: segment.cnn,
                                  street: segment.streetname,
                                  classcode: segment.classcode,
                                  length: segment.length,
                                  cl_longitudes: segment.cl_longitudes,
                                  cl_latitudes: segment.cl_latitudes,
                                  cl_lengths: segment.cl_lengths,
                                  average_speed: segment.speed_limit,
                                  expected_time: segment.time_at_speed_limit,
                                  last_update_ts: null,
                                  speed_limit: segment.speed_limit,
                                  time_at_speed_limit: segment.time_at_speed_limit,
                                  speed_limit_mph: segment.speed_limit_mph}]->(t)
               ''', segments=processed_segments)

    r.summary()

    print "Creating intersections index"
    r = db.run('CREATE INDEX ON :Segment(cnn)')
    r.summary()

    print "Done"

if __name__ == '__main__':
        main()
