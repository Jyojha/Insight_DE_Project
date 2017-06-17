from neo4j.v1 import GraphDatabase, basic_auth
from config import settings

import log

logger = log.get_logger()

driver = GraphDatabase.driver(settings.DB_URL,
                              auth=basic_auth(settings.USER_NAME,
                                              settings.USER_PASSWORD))

if settings.SHORTEST_PATH_ALGO == 'dijkstra':
    FIND_PATH_QUERY='''MATCH (n:Intersection {cnn: $from_cnn})
                       WITH n
                       MATCH (m:Intersection {cnn: $to_cnn})
                       CALL apoc.algo.dijkstraWithDefaultWeight(n, m, 'Segment>', 'expected_time', 1200)
                       YIELD path, weight
                       RETURN path, weight'''
elif settings.SHORTEST_PATH_ALGO == 'aStar':
    FIND_PATH_QUERY='''MATCH (n:Intersection {cnn: $from_cnn})
                       WITH n
                       MATCH (m:Intersection {cnn: $to_cnn})
                       CALL apoc.algo.aStar(n, m, 'Segment>', 'length', 'lat', 'lon')
                       YIELD path, weight
                       RETURN path, weight'''
else:
    algo = settings.SHORTEST_PATH_ALGO
    raise AssertionError("Unknown shortest path algorithm %s" % algo)

def find_path(from_cnn, to_cnn):
    with driver.session() as db:
        r = db.run(FIND_PATH_QUERY, from_cnn=from_cnn, to_cnn=to_cnn)

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
            from_coords = (from_node['lat'], from_node['lon'])
            to_name = to_node['name']
            to_cnn = to_node['cnn']
            to_coords = (to_node['lat'], to_node['lon'])
            street = rel['street']
            centerline = zip(rel['cl_latitudes'], rel['cl_longitudes'])
            length = rel['length']

            avg_speed = rel.get('average_speed')
            expected_time = rel.get('expected_time')

            from_node = to_node

            resp_item = {'from_name': from_name,
                         'from_cnn': from_cnn,
                         'from_coords': from_coords,
                         'to_name': to_name,
                         'to_cnn': to_cnn,
                         'to_coords': to_coords,
                         'street': street,
                         'centerline': centerline,
                         'length': length,
                         'average_speed': avg_speed,
                         'expected_time': expected_time}

            result.append(resp_item)

        return result

def update_times(items):
    updates = []

    for street, direction, expected_time, avg_speed in items:
        update = {}

        from_cnn = street.from_cnn
        to_cnn   = street.to_cnn

        if direction == 'T':
            from_cnn, to_cnn = to_cnn, from_cnn

        update['from']  = from_cnn
        update['to']    = to_cnn
        update['time']  = expected_time
        update['speed'] = avg_speed

        updates.append(update)

    with driver.session() as db:
        r = db.run('''UNWIND {updates} as update
                      MATCH (f:Intersection {cnn: update.from}),
                            (t:Intersection {cnn: update.to}),
                            (f)-[s:Segment]->(t)
                      SET s.expected_time = update.time,
                          s.avg_speed = update.speed
                      RETURN s''', updates=updates)

        try:
            r.summary()
        except Exception, e:
            import traceback

            trace = traceback.format_exc()
            logger.error('Failed to update neo4j graph %s:\n%s' % (e, trace))
            return

        logger.debug('Successfully updated %d neo4j graph edges' % len(updates))

def find_matching_streets(name):
    with driver.session() as db:
        pattern = '(?i)%s.*' % name
        match_strtseg = db.run('''Match ()-[s:Segment]-()
                                  WHERE s.street =~ {pattern}
                                  RETURN DISTINCT s.street AS street
                                  ORDER BY s.street
                                  LIMIT 20''', pattern=pattern)

        result = []
        for row in match_strtseg.records():
            result.append(row['street'])

        return result

def find_street_intersections(street):
    with driver.session() as db:
        match_intersection = db.run('''Match (m)-[s:Segment]-(n)
                                        WHERE s.street = {street}
                                        RETURN DISTINCT m.name as intersecting_strt,
                                        m.cnn as cnn''', street=street)


        result = []
        for intersection in match_intersection.records():
            intersecting = intersection['intersecting_strt']
            cnn = intersection['cnn']

            result.extend([(name, cnn) for name in intersecting if name != street])

        return result


