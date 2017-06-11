from numpy import array, cross, dot
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

    def __repr__(self):
        return 'StreetSegment(%d, "%s")' % (self.cnn, self.name)

class IndexItem(object):
    def __init__(self, src, dst, src_xyz, dst_xyz, obj):
        self.src = src
        self.dst = dst
        self.src_xyz = src_xyz
        self.dst_xyz = dst_xyz
        self.obj = obj

    def __repr__(self):
        return 'IndexItem%s' % str((self.src, self.dst,
                                    self.src_xyz, self.dst_xyz,
                                    self.obj))

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

    def _bbox_for_point(self, xyz, radius):
        x, y, z = xyz

        return (x - radius, x + radius,
                y - radius, y + radius,
                z - radius, z + radius)

    def _point_segment_distance(self, point, s1, s2):
        point = array(point)

        # If the dot product is less than 0, this means that the perpendicular
        # from the point lies outside the segment (the angle at s1 is greater
        # than 90 degrees). So we use the distance to the corresponding end of
        # the segment instead.
        dot1 = dot(point - s1, s2 - s1)
        if dot1 < 0:
            return norm(point - s1)

        # Same as above, just for the other end.
        dot2 = dot(point - s2, s1 - s2)
        if dot2 < 0:
            return norm(point - s2)

        # Otherwise, the shortest distance is the length of perpendicular to
        # the segment line.
        return norm(cross(s1 - point, s2 - point)) / norm(s2 - s1)

    def add_street_segment(self, id, obj, segment):
        for node1, node2 in zip(segment, segment[1:]):
            xyz1 = self._toXYZ(node1)
            xyz2 = self._toXYZ(node2)
            bbox = self._bbox(xyz1, xyz2)

            item = IndexItem(node1, node2, array(xyz1), array(xyz2), obj)
            self._rtree.insert(id, bbox, obj=item)

    def nearest_segments(self, lon, lat, radius=10, num=2):
        xyz = self._toXYZ((lon, lat))
        bbox = self._bbox_for_point(xyz, radius)

        nearest_segments_list = []
        for item in self._rtree.intersection(bbox, objects=True):
            dist = self._point_segment_distance(xyz,
                                                item.object.src_xyz,
                                                item.object.dst_xyz)
            if dist <= radius:
                nearest_segments_list.append((dist, item.id, item.object))

        nearest_segments_list.sort(key=lambda x: x[0])

        return nearest_segments_list[:num]

    def import_from_file(self, path=settings.SEGMENT_PATH):
        segments = read_segments(path)

        for segment in segments:
            cnn = segment['cnn']
            centerline = segment['centerline']
            name = segment['streetname']

            self.add_street_segment(cnn, StreetSegment(cnn, name), centerline)
