import pandas as pd
from copy import deepcopy

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

def read_segments(path=settings.SEGMENT_PATH):
    segments = pd.read_pickle(path)
    return df_to_dict(normalize_centerlines(segments))

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

def post_process_segments(segments):
    massaged = []

    for segment in segments:
        centerline = segment['centerline']
        longitudes = [x[0] for x in centerline]
        latitudes  = [x[1] for x in centerline]

        template = {'cnn': segment['cnn'],
                    'streetname': segment['streetname'],
                    'classcode': segment['classcode'],
                    'longitudes': longitudes,
                    'latitudes': latitudes,
                    'length': segment['length']}

        t, f = segment["to_cnn"], segment["from_cnn"]

        if segment['oneway'] in ['B', 'T']:
            cleaned = deepcopy(template)

            cleaned['from_cnn'] = t
            cleaned['to_cnn']   = f

            # After normalization centerline always starts at "from
            # intersection", so we need to reverse it back to preserve this
            # property.
            cleaned['longitudes'].reverse()
            cleaned['latitudes'].reverse()

            massaged.append(cleaned)

        if segment['oneway'] in ['B', 'F']:
            cleaned = deepcopy(template)

            cleaned['from_cnn'] = f
            cleaned['to_cnn']   = t

            massaged.append(cleaned)

    return massaged
