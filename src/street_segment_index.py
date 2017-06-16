import cPickle

from numpy import array, cross, dot
from numpy.linalg import norm
from scipy.spatial.distance import euclidean

from pysal.cg.sphere import toXYZ, RADIUS_EARTH_KM
from rtree.index import Index, Property


import log

from data_utils import read_segments, get_resource
from config import settings
from utils import timeit

logger = log.get_logger()

RADIUS_EARTH_M = RADIUS_EARTH_KM * 1000

class StreetSegment(object):
    def __init__(self, cnn, name):
        self.cnn = cnn
        self.name = name

    def __repr__(self):
        return 'StreetSegment(%d, "%s")' % (self.cnn, self.name)

class IndexItem(object):
    def __init__(self, src, dst, subsegment_index, src_xyz, dst_xyz, obj):
        self.src = src
        self.dst = dst

        self.subsegment_index = subsegment_index

        self.src_xyz = src_xyz
        self.dst_xyz = dst_xyz
        self.obj = obj

    def __repr__(self):
        return 'IndexItem%s' % str((self.src, self.dst,
                                    self.subsegment_index,
                                    self.src_xyz, self.dst_xyz,
                                    self.obj))

class SerializableIndex(Index):
    def __init__(self, *args, **kwargs):
        self._serialize_objects = True
        super(SerializableIndex, self).__init__(*args, **kwargs)

    def __getstate__(self):
        state = super(SerializableIndex, self).__getstate__()
        state['rtree_dump'] = self._dump_rtree()

        return state

    def __setstate__(self, state):
        rtree_dump = state.pop('rtree_dump')
        super(SerializableIndex, self).__setstate__(state)
        self._undump_rtree(rtree_dump)

    def dumps(self, obj):
        if self._serialize_objects:
            return cPickle.dumps(obj, protocol=cPickle.HIGHEST_PROTOCOL)
        else:
            return obj

    def loads(self, data):
        if self._serialize_objects:
            return cPickle.loads(data)
        else:
            return data

    def _disable_serialization(self, f, *args, **kwargs):
        self._serialize_objects = False
        r = f(*args, **kwargs)
        self._serialize_objects = True

        return r

    def _dump_rtree(self):
        dt, dump = timeit(lambda: self._disable_serialization(self._do_dump_rtree))
        logger.debug('Dumped r-tree in %fs', dt)

        return dump

    def _do_dump_rtree(self):
        result = []

        bounds = self.get_bounds()
        for item in self.intersection(bounds, objects=True):
            result.append( (item.id, item.bbox, item.object) )

        return result

    def _undump_rtree(self, items):
        dt, r = timeit(lambda:  self._disable_serialization(self._do_undump_rtree, items))
        logger.debug('Undumped r-tree in %fs', dt)

        return r

    def _do_undump_rtree(self, items):
        self.handle = self._create_idx_from_stream(iter(items))

class StreetSegmentIndex(object):
    def __init__(self, _segments=[]):
        props = Property()
        props.dimension = 3

        kwargs = {'properties': props}

        if _segments:
            self._rtree = SerializableIndex(self._generate_segments(_segments), **kwargs)
        else:
            self._rtree = SerializableIndex(**kwargs)

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

        return (minx, miny, minz, maxx, maxy, maxz)

    def _bbox_for_point(self, xyz, radius):
        x, y, z = xyz

        return (x - radius,
                y - radius,
                z - radius,
                x + radius,
                y + radius,
                z + radius)

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

    def _generate_segments(self, segments):
        for segment in segments:
            cnn = segment['cnn']
            centerline = segment['centerline']
            name = segment['streetname']

            subsegments = self._generate_subsegments(cnn,
                                                     StreetSegment(cnn, name),
                                                     centerline)
            for item in subsegments:
                yield item

    def _generate_subsegments(self, id, obj, segment):
        for ix, (node1, node2) in enumerate(zip(segment, segment[1:])):
            xyz1 = self._toXYZ(node1)
            xyz2 = self._toXYZ(node2)
            bbox = self._bbox(xyz1, xyz2)

            yield (id, bbox, IndexItem(node1, node2, ix,
                                       array(xyz1), array(xyz2), obj))

    def add_street_segment(self, id, obj, segment):
        for id, bbox, item in self._generate_subsegments(id, obj, segment):
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

    @classmethod
    def from_segments(cls, path=settings.SEGMENTS_PATH):
        return cls(_segments=read_segments(path))

    @classmethod
    def read_pickle(cls, path=settings.STREET_INDEX_PICKLE):
        dt, index = timeit(lambda: cPickle.load(get_resource(path)))

        logger.debug("Read street index from resource in %fs", dt)

        if not isinstance(index, cls):
            raise TypeError('"%s" is not a pickled street index' % path)

        return index

    def write_pickle(self, path=settings.STREET_INDEX_PICKLE):
        with open(path, 'w') as f:
            cPickle.dump(self, f, protocol=cPickle.HIGHEST_PROTOCOL)

if __name__ == '__main__':
    import sys

    index = StreetSegmentIndex.read_pickle()

    for line in sys.stdin.readlines():
        line = line.strip()
        fields = line.split(" ")

        lat = float(fields[0])
        lon = float(fields[1])

        segments = index.nearest_segments(lon, lat, radius=10, num=4)

        if not segments:
            print "%s | <not found>" % line
            continue

        matches = []
        for d, cnn, segment in segments:
            matches.append("dist=%f, cnn=%d name='%s'" % (d, cnn, segment.obj.name))

        print "%s | %s" % (line, ' | '.join(matches))
