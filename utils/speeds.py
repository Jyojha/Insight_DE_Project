#!/usr/bin/env python2
import json
from os import path
from sys import stderr, stdout

ROOT_DIR = path.abspath(path.join(path.dirname(__file__), '..'))
DATA_DIR = path.join(ROOT_DIR, 'misc')
KNOWN_SPEEDS_PATH = path.join(DATA_DIR, 'known_speed_limits.json')
STREETS_PATH = path.join(DATA_DIR,
                         'San Francisco Basemap Street Centerlines.geojson')

FREEWAY_CLASSCODE = 1

FREEWAY_SPEED = 65
DEFAULT_SPEED = 25

known_speeds = json.loads(open(KNOWN_SPEEDS_PATH, 'r').read())

speed_by_cnn = dict( (item['cnn'], item['limit']) for item in known_speeds )

speed_by_name = {}
for item in known_speeds:
    name = item['name']
    limit = item['limit']

    speeds = speed_by_name.setdefault(name, [])
    speeds.append(limit)

for street in speed_by_name:
    speed_by_name[street] = min(speed_by_name[street])

final_speeds = []

stat_cnn_match = 0
stat_name_match = 0
stat_classcode_match = 0
stat_default_match = 0

for street in json.loads(open(STREETS_PATH, 'r').read())['features']:
    street = street['properties']
    name = street['street']
    full_name = street['streetname']
    cnn = int(float(street['cnn']))
    classcode = int(street['classcode'])

    if cnn in speed_by_cnn:
        speed = speed_by_cnn[cnn]
        source = 'cnn'
        stat_cnn_match += 1
    elif name in speed_by_name:
        speed = speed_by_name[name]
        source = 'name'
        stat_name_match += 1
    elif classcode == FREEWAY_CLASSCODE:
        speed = FREEWAY_SPEED
        source = 'classcode'
        stat_classcode_match += 1
    else:
        speed = DEFAULT_SPEED
        source = 'default'
        stat_default_match += 1

    obj = {'name': name,
           'full_name': full_name,
           'source': source,
           'speed': speed,
           'cnn': cnn,
           'classcode': classcode}

    final_speeds.append(obj)

final_speeds.sort(key=lambda obj: obj['full_name'])

print >> stderr, 'Stats:\n'
print >> stderr, '  matched by cnn: %d' % stat_cnn_match
print >> stderr, '  matched by name: %d' % stat_name_match
print >> stderr, '  matched by classcode: %d' % stat_classcode_match
print >> stderr, '  default used: %d' % stat_default_match
print >> stderr
print >> stderr, 'Total: %d'  % len(final_speeds)

stdout.write(json.dumps(final_speeds, indent=2))
