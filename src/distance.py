# For details see http://www.movable-type.co.uk/scripts/gis-faq-5.1.html

from math import asin, sin, cos, sqrt, radians

from config import settings


# Haight St and Central Ave
lonlat1 = (-122.44364908616127, 37.77042637070029)

# Haight St and Masonic Ave
lonlat2 = (-122.4453449903129, 37.77021017487183)


# in meters
EARTH_RADIUS = 6367000

def haversin(x, y, R=EARTH_RADIUS):
    lon1, lat1 = x[0], x[1]
    lon2, lat2 = y[0], y[1]

    lon1, lat1, lon2, lat2 = map(radians, (lon1, lat1, lon2, lat2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(min(1,sqrt(a)))

    return R * c

def haversin_polyline(points):
    return sum(haversin(x, y) for x, y in zip(points, points[1:]))

class StreetInfo(object):
    def __init__(self, props):
        self.cnn                = props['cnn']
        self.oneway             = props['oneway']
        self.centerline         = props['centerline']
        self.centerline_lengths = props['centerline_lengths']
        self.name               = props['streetname']
        self.length             = props['length']
        self.classcode          = props['classcode']
        self.from_coords        = props['from_cnn_coords']
        self.to_coords          = props['to_cnn_coords']

        self.subsegments = zip(self.centerline, self.centerline[1:])

    def find_distance(self, (start_ix, start_coords), (end_ix, end_coords)):
        if start_ix == end_ix:
            return haversin(start_coords, end_coords)

        if start_ix > end_ix:
            start_ix, end_ix = end_ix, start_ix
            start_coords, end_coords = end_coords, start_coords

        dist = 0
        for ix in range(start_ix + 1, end_ix):
            dist += self.centerline_lengths[ix]

        start_subsegment = self.subsegments[start_ix]
        end_subsegment   = self.subsegments[end_ix]

        dist += haversin(start_coords, start_subsegment[1])
        dist += haversin(end_coords, end_subsegment[0])

        return dist

    def get_direction(self, (start_ix, start_coords), (end_ix, end_coords)):
        direction = None

        if start_ix < end_ix:
            direction = 'F'
        elif end_ix < start_ix:
            direction = 'T'
        else:
            subsegment  = self.subsegments[start_ix]
            from_coords = subsegment[0]

            start_to_from = haversin(from_coords, start_coords)
            end_to_from   = haversin(from_coords, end_coords)

            if start_to_from < end_to_from:
                direction = 'F'
            else:               # TODO
                direction = 'T'

        return self._check_computed_direction(direction)

    def _check_computed_direction(self, direction):
        if self.oneway == 'B':
            return direction

        if self.oneway == direction:
            return direction

        return None

    def __repr__(self):
        return 'StreetInfo(**%s)' % self.__dict__

class CarTracker(object):
    def __init__(self, path=settings.SEGMENTS_PATH):
        from data_utils import read_segments

        segments = read_segments(path)

        self._index = {}
        for segment in segments:
            info = StreetInfo(segment)
            self._index[info.cnn] = info

    def get_distance(self, start_event, start_segment, end_event, end_segment):
        start_coords = [start_event.lon, start_event.lat]
        end_coords   = [end_event.lon, end_event.lat]

        cnn     = start_segment.obj.cnn
        end_cnn = end_segment.obj.cnn

        if cnn != end_cnn:
            raise AssertionError("start cnn %s is different "
                                 "from end cnn" % (cnn, end_cnn))

        start_ix = start_segment.subsegment_index
        end_ix   = end_segment.subsegment_index

        street = self._index[cnn]


        start = (start_ix, start_coords)
        end   = (end_ix, end_coords)

        distance  = street.find_distance(start, end)
        direction = street.get_direction(start, end)

        return distance, direction
