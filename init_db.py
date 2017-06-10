import pandas as pd
from neo4j.v1 import GraphDatabase, basic_auth
from config import settings


# function to convert each row item in dictionary
def df_to_dict(df):
    return df.to_dict(orient='records')

def extract_intersections(segments_list):
    intersection_dict = {}
    intersection_name = {}

    for item in segments_list:

        if item['from_cnn'] not in intersection_dict:
            intersection_dict[item['from_cnn']] = item['from_cnn_coords']
            intersection_name[item['from_cnn']] = []

        intersection_name[item['from_cnn']].append(item['streetname'])


        if item['to_cnn'] not in intersection_dict:
            intersection_dict[item['to_cnn']] = item['to_cnn_coords']
            intersection_name[item['to_cnn']] = []

        intersection_name[item['to_cnn']].append(item['streetname'])

    intersections = []

    for key, value in intersection_dict.iteritems():
        tmp_dict = {}
        tmp_dict['cnn'] = key
        tmp_dict['lon'] = value[0]
        tmp_dict['lat'] = value[1]
        tmp_dict['name'] = list(set(intersection_name[key]))
        intersections.append(tmp_dict)

    return intersections

def massage_segments(segments):
    massaged = []

    for segment in segments:
        centerline = segment['centerline']
        longitudes = [x[0] for x in centerline]
        latitudes  = [x[1] for x in centerline]

        cleaned = {'cnn': segment['cnn'],
                   'streetname': segment['streetname'],
                   'classcode': segment['classcode'],
                   'longitudes': longitudes,
                   'latitudes': latitudes,
                   'length': segment['length']}

        t, f = segment["to_cnn"], segment["from_cnn"]

        if segment['oneway'] in ['B', 'T']:
            cleaned['from_cnn'] = t
            cleaned['to_cnn']   = f

            massaged.append(cleaned.copy())

        if segment['oneway'] in ['B', 'F']:
            cleaned['from_cnn'] = f
            cleaned['to_cnn']   = t

            massaged.append(cleaned)

    return massaged

def main():
    '''Populate the static road network data in to the database'''

    # Read the data
    segments = pd.read_pickle(settings.SEGMENT_PATH)
    node_neighbors = pd.read_json(settings.NODE_NEIGHBORS_PATH, orient='records')

    # Define the entry point to the database
    driver = GraphDatabase.driver(settings.DB_URL,
                                  auth=basic_auth(settings.USER_NAME,
                                                  settings.USER_PASSWORD))
    db = driver.session()

    print "Deleting everything"
    db.run("MATCH (n) DETACH DELETE n")

    segments_list = df_to_dict(segments)
    nodes = extract_intersections(segments_list)

    massaged_segments = massage_segments(segments_list)

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
    r = db.run('''UNWIND {segments} as segment
                  MATCH (f:Intersection {cnn: segment.from_cnn}),
                        (t:Intersection {cnn: segment.to_cnn})
                  CREATE (f)-[s:Segment {cnn: segment.cnn,
                                         street: segment.streetname,
                                         classcode: segment.classcode,
                                         length: segment.length,
                                         longitudes: segment.longitudes,
                                         latitudes: segment.latitudes}]->(t)
               ''', segments=massaged_segments)

    r.summary()

    print "Creating intersections index"
    r = db.run('CREATE INDEX ON :Segment(cnn)')
    r.summary()

    print "Done"

if __name__ == '__main__':
        main()
