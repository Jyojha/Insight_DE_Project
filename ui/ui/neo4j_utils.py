from neo4j.v1 import GraphDatabase, basic_auth
from django.conf import settings

driver = GraphDatabase.driver(settings.DB_URL,
                              auth=basic_auth(settings.USER_NAME,
                                              settings.USER_PASSWORD))

def find_path(from_cnn, to_cnn):
    with driver.session() as db:
        r = db.run('''MATCH (n:Intersection {cnn: $from_cnn})
                      WITH n
                      MATCH (m:Intersection {cnn: $to_cnn})
                      CALL apoc.algo.dijkstra(n, m, 'Segment>', 'length')
                      YIELD path, weight
                      RETURN path, weight''',
                   from_cnn=from_cnn, to_cnn=to_cnn)

        row = r.single()

        if row is None:
                return None

        weight = row['weight']
        path = row['path']

        rels = path.relationships
        nodes = path.nodes

        result = []
        from_node = nodes[0]

        for to_node, rel in zip(nodes[1:], rels):
            from_name = from_node['name']
            from_cnn = from_node['cnn']
            to_name = to_node['name']
            to_cnn = to_node['cnn']
            street = rel['street']
            centerline = zip(rel['longitudes'], rel['latitudes'])
            length = rel['length']

            from_node = to_node

            resp_item = {'from_name': from_name,
                         'from_cnn': from_cnn,
                         'to_name': to_name,
                         'to_cnn': to_cnn,
                         'street': street,
                         'centerline': centerline,
                         'length': length}

            result.append(resp_item)

        return result
