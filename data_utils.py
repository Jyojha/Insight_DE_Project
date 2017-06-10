import pandas as pd
from config import settings

# function to convert each row item in dictionary
def df_to_dict(df):
    return df.to_dict(orient='records')

def read_segments(path=settings.SEGMENT_PATH):
    segments = pd.read_pickle(path)
    return df_to_dict(segments)

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
