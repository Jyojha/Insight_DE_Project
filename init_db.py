import pandas as pd
from neo4j.v1 import GraphDatabase, basic_auth
import settings


# function to convert each row item in dictionary
def df_to_dict(df):
    return df.to_dict(orient='records')

def extract_intersections(edges_list):
    intersection_dict = {}
    intersection_name = {}

    for item in edges_list:

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
        tmp_dict['coordinates'] = value
        tmp_dict['name'] = list(set(intersection_name[key]))
        intersections.append(tmp_dict)

    return intersections

def massage_edges(edges):
    massaged = []

    for edge in edges:
        centerline = edge['centerline']
        longitudes = [x[0] for x in centerline]
        latitudes  = [x[1] for x in centerline]

        cleaned = {'cnn': edge['cnn'],
                   'streetname': edge['streetname'],
                   'classcode': edge['classcode'],
                   'longitudes': longitudes,
                   'latitudes': latitudes,
                   'length': edge['length']}

        t, f = edge["to_cnn"], edge["from_cnn"]

        if edge['oneway'] in ['B', 'T']:
            cleaned['from_cnn'] = t
            cleaned['to_cnn']   = f

            massaged.append(cleaned.copy())

        if edge['oneway'] in ['B', 'F']:
            cleaned['from_cnn'] = f
            cleaned['to_cnn']   = t

            massaged.append(cleaned)

    return massaged

def main():
    '''Populate the static road network data in to the database'''

    # Read the data
    edges = pd.read_pickle(settings.EDGE_PATH)
    node_neighbors = pd.read_json(settings.NODE_NEIGHBORS_PATH, orient='records')

    # Define the entry point to the database
    driver = GraphDatabase.driver(settings.DB_URL,
                                  auth=basic_auth(settings.USER_NAME,
                                                  settings.USER_PASSWORD))
    db = driver.session()

    print "Deleting everything"
    db.run("MATCH (n) DETACH DELETE n")

    edges_list = df_to_dict(edges)
    nodes = extract_intersections(edges_list)

    massaged_edges = massage_edges(edges_list)

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
    r = db.run('''UNWIND {edges} as edge
                  MATCH (f:Intersection {cnn: edge.from_cnn}),
                        (t:Intersection {cnn: edge.to_cnn})
                  CREATE (f)-[s:Segment {cnn: edge.cnn,
                                         street: edge.streetname,
                                         classcode: edge.classcode,
                                         length: edge.length,
                                         longitudes: edge.longitudes,
                                         latitudes: edge.latitudes}]->(t)
               ''', edges=massaged_edges)

    r.summary()

    print "Creating intersections index"
    r = db.run('CREATE INDEX ON :Segment(cnn)')
    r.summary()

    print "Done"

if __name__ == '__main__':
        main()
