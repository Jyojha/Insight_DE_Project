from numpy import array, cross
from numpy.linalg import norm
from scipy.spatial.distance import euclidean

from pysal.cg.sphere import toXYZ, RADIUS_EARTH_KM
from rtree.index import Index, Property

from data_utils import read_segments
from config import settings

RADIUS_EARTH_M = RADIUS_EARTH_KM * 1000

class StreetSegment(object):
    def __init__(self, cnn, name):
        self.cnn = cnn
        self.name = name

class StreetSegmentIndex(object):

    def __init__(self):
        props = Property()
        props.dimension = 3

        self._rtree = Index(interleaved=False, properties=props)

    def _toXYZ(self, point):
        x, y, z = toXYZ(point)

        return (x * RADIUS_EARTH_M, y * RADIUS_EARTH_M, z * RADIUS_EARTH_M)

    def _bbox(self, xyz1, xyz2):
        x1, y1, z1 = xyz1
        x2, y2, z2 = xyz2

        minx = min(x1, x2)
        miny = min(y1, y2)
        minz = min(z1, z2)

        maxx = max(x1, x2)
        maxy = max(y1, y2)
        maxz = max(z1, z2)

        return (minx, maxx, miny, maxy, minz, maxz)

    def _point_line_distance(self, point, s1, s2):
        point = array(point)

        return norm(cross(s1 - point, s2 - point)) / norm(s2 - s1)

    def add_street_segment(self, id, obj, segment):
        for node1, node2 in zip(segment, segment[1:]):
            xyz1 = self._toXYZ(node1)
            xyz2 = self._toXYZ(node2)
            bbox = self._bbox(xyz1, xyz2)

            self._rtree.insert(id, bbox, obj=(array(xyz1), array(xyz2), obj))

    def nearest_segments(self, lon, lat, radius=20, num=2):
        x, y, z = self._toXYZ((lon, lat))

        bbox = (x - radius, x + radius,
                y - radius, y + radius,
                z - radius, z + radius)

        nearest_segments_list = []
        for item in self._rtree.intersection(bbox, objects=True):

            tmp_dist = self._point_line_distance((x, y, z), item.object[0], item.object[1])

            if tmp_dist <= radius:
                nearest_segments_list.append((tmp_dist, item.id, item.object[2]))

        nearest_segments_list.sort(key=lambda x: x[0])

        return nearest_segments_list[0:num]

    def import_from_file(self, path=settings.SEGMENT_PATH):
        segments = read_segments(path)

        for segment in segments:
            cnn = segment['cnn']
            centerline = segment['centerline']
            name = segment['streetname']

            self.add_street_segment(cnn, StreetSegment(cnn, name), centerline)
