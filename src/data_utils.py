import json

import pandas as pd
from scipy import constants
from copy import deepcopy
from pkg_resources import resource_stream

from config import settings
from distance import haversin

# function to convert each row item in dictionary
def df_to_dict(df):
    return df.to_dict(orient='records')

def normalize_centerlines(segments):
    def maybe_reverse(row):
        centerline = row['centerline']
        to_coords = row['to_cnn_coords']
        from_coords = row['from_cnn_coords']

        from_dist = haversin(centerline[0], from_coords)
        to_dist = haversin(centerline[0], to_coords)

        if from_dist > to_dist:
            return centerline[::-1]
        else:
            return centerline

    subset = segments[['centerline', 'from_cnn_coords', 'to_cnn_coords']]
    segments['centerline'] = subset.apply(maybe_reverse, axis=1)

    return segments

def add_centerline_lengths(segments):
    def compute_dists(points):
        return [haversin(x, y) for x, y in zip(points, points[1:])]

    segments['centerline_lengths'] = segments['centerline'].map(compute_dists)
    return segments

def read_segments(path=settings.SEGMENTS_PATH):
    segments = normalize_centerlines(pd.read_pickle(get_resource(path)))
    return df_to_dict(add_centerline_lengths(segments))

def read_speed_limits(path=settings.SPEED_LIMITS_PATH):
    with open(path, 'r') as f:
        return dict((item['cnn'], item['speed']) for item in json.load(f))

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

def mph2metersps(miles):
    return (miles * constants.mile) / constants.hour

def post_process_segments(segments, speeds):
    massaged = []

    for segment in segments:
        centerline = segment['centerline']
        longitudes = [x[0] for x in centerline]
        latitudes  = [x[1] for x in centerline]

        cnn = segment['cnn']
        length = segment['length']
        speed_limit_mph = speeds[cnn]
        speed_limit_mps = mph2metersps(speed_limit_mph)
        time_at_speed_limit = length / speed_limit_mps

        template = {'cnn': cnn,
                    'streetname': segment['streetname'],
                    'classcode': segment['classcode'],
                    'cl_longitudes': longitudes,
                    'cl_latitudes': latitudes,
                    'cl_lengths': segment['centerline_lengths'],
                    'length': segment['length'],
                    'speed_limit': speed_limit_mps,
                    'speed_limit_mph': speed_limit_mph,
                    'time_at_speed_limit': time_at_speed_limit}

        t, f = segment["to_cnn"], segment["from_cnn"]

        if segment['oneway'] in ['B', 'T']:
            cleaned = deepcopy(template)

            cleaned['from_cnn'] = t
            cleaned['to_cnn']   = f

            # After normalization centerline always starts at "from
            # intersection", so we need to reverse it back to preserve this
            # property.
            cleaned['cl_longitudes'].reverse()
            cleaned['cl_latitudes'].reverse()
            cleaned['cl_lengths'].reverse()

            massaged.append(cleaned)

        if segment['oneway'] in ['B', 'F']:
            cleaned = deepcopy(template)

            cleaned['from_cnn'] = f
            cleaned['to_cnn']   = t

            massaged.append(cleaned)

    return massaged

def get_resource(path):
    return resource_stream(__name__, path)
