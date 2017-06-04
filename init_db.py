import pandas as pd
from neo4j.v1 import GraphDatabase, basic_auth
import settings


# function to convert each row item in dictionary
def df_to_dict(df):
    return df.to_dict(orient='records')
    
def extract_intersections(edges_list):
    intersection_dict = {}

    for item in edges_list:

        if item['from_cnn'] not in intersection_dict:
            intersection_dict[item['from_cnn']] = item['from_cnn_coords']

        if item['to_cnn'] not in intersection_dict:
            intersection_dict[item['to_cnn']] = item['to_cnn_coords']
    
    intersections = []

    for key, value in intersection_dict.iteritems():
        tmp_dict = {}
        tmp_dict['cnn'] = key
        tmp_dict['coordinates'] = value
        intersections.append(tmp_dict)

    return intersections
            




def main():
    ''' Populate the static road network data in to the database'''
    
    # Read the data
    edges = pd.read_pickle(settings.EDGE_PATH)
    node_neighbors = pd.read_json(settings.NODE_NEIGHBORS_PATH, orient='records')
    
    # Define the entry point to the database
    driver = GraphDatabase.driver(settings.DB_URL, 
                                  auth=basic_auth(settings.USER_NAME, settings.USER_PASSWORD))
    db = driver.session()

    db.run("MATCH (n) DETACH DELETE n")
    
    edges_list = df_to_dict(edges)
    nodes = extract_intersections(edges_list)

    r = db.run('''UNWIND {nodes} as node
                  CREATE (n:Intersection)
                  SET n = node
               ''', nodes=nodes)
    print r.summary()

    r = db.run('CREATE INDEX ON :Intersection(cnn)')
    print r.summary()

    r = db.run('''UNWIND {edges} as edge
                  MATCH (f:Intersection {cnn: edge.from_cnn}),
                        (t:Intersection {cnn: edge.to_cnn})
                  CREATE (f)-[s:Segment {cnn: edge.cnn, from_cnn: edge.from_cnn, to_cnn: edge.to_cnn, from_coordinates: edge.from_cnn_coords, to_coordinates: edge.to_cnn_coords, street: edge.streetname, classcode: edge.classcode, length: edge.length}]->(t)
               ''', edges=edges_list)

    print r.summary()



if __name__ == '__main__':
        main()

        
