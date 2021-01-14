import inspect

import numpy as np
from copy import copy, deepcopy
from math import isclose
from tcysim.utils.vector cimport RotateOperator, TEU, V3
from tcysim.utils.math cimport feq

cdef class LayoutItem:
    cdef readonly V3 offset
    cdef readonly V3 size
    cdef readonly double rotate
    cdef readonly RotateOperator rtt_operator
    cdef readonly RotateOperator r_rtt_operator

    def __init__(self,
                 V3 offset=V3.zero(),
                 V3 size=V3.one(),
                 double rotate=0,
                 **kwargs,
                 ):
        self.offset = offset.clone()
        self.size = size.clone()
        self.rotate = rotate
        self.rtt_operator = RotateOperator(rotate)
        self.r_rtt_operator = RotateOperator(-rotate)

    def __mul__(self, num):
        return [deepcopy(self) for _ in range(num)]

    def __contains__(self, self_coord):
        return V3.zero() <= self_coord <= self.size

    cpdef move(self, V3 offset, double rotate=0):
        self.offset = offset.clone()
        self.rotate = rotate.clone()
        self.rtt_operator = RotateOperator(rotate)
        self.r_rtt_operator = RotateOperator(-rotate)

    cpdef V3 coord_l2g(self, V3 local_offset):
        return local_offset.rotate(self.rtt_operator).iadd(self.offset)

    cpdef V3 coord_g2l(self, V3 global_offset):
        return global_offset.sub(self.offset).rotate(self.r_rtt_operator)

    cpdef V3 center_coord(self, transform_to=None):
        cdef V3 size = self.size
        return self.transform_to_no_copy(V3(size.x / 2, size.y / 2, size.z / 2), transform_to)

    cpdef V3 top_coord(self, transform_to=None):
        cdef V3 size = self.size
        return self.transform_to_no_copy(V3(size.x / 2, size.y / 2, size.z), transform_to)

    cpdef V3 bottom_coord(self, transform_to=None):
        cdef V3 size = self.size
        return self.transform_to_no_copy(V3(size.x / 2, size.y / 2, 0), transform_to)

    cpdef V3 transform_to(self, V3 coord, other=None):
        cdef LayoutItem o
        if other is None:
            return coord.clone()
        elif other == "g":
            return self.coord_l2g(coord)
        else:
            if isinstance(other, LayoutItem):
                o = other
            else:
                o = other.layout
            if feq(self.rotate, o.rotate):
                # if -1e-3 < self.rotate - o.rotate < 1e-3:
                return o.coord_g2l(self.offset).iadd(coord)
            else:
                return o.coord_g2l(self.coord_l2g(coord))

    cpdef V3 transform_to_no_copy(self, V3 coord, other=None):
        cdef LayoutItem o
        if other is None:
            return coord
        elif other == "g":
            return self.coord_l2g(coord)
        else:
            if isinstance(other, LayoutItem):
                o = other
            else:
                o = other.layout
            if feq(self.rotate, o.rotate):
                # if -1e-3 < self.rotate - o.rotate < 1e-3:
                return o.coord_g2l(self.offset).iadd(coord)
            else:
                return o.coord_g2l(self.coord_l2g(coord))


class ItemWithAnchors:
    Anchors = None

    def __init__(self, *args, **kwargs):
        self.__anchors = None

    def add_anchor(self, name, anchor):
        if self.__anchors is None:
            self.__anchors = {}
        self.__anchors[name] = anchor
        
    def get_anchor(self, name, transform_to=None):
        cdef V3 anchor
        if self.__anchors is not None and name in self.__anchors:
            anchor = self.__anchors[name]
        else:
            if self.ANCHORS is not None and name in self.ANCHORS:
                anchor = self.ANCHORS[name]
            else:
                 for base_class in inspect.getmro(self.__class__):
                     anchors = base_class.__dict__.get("ANCHORS", None)
                     if anchors is not None:
                         anchor = anchors[name]
        return self.transform_to(anchor, transform_to)


class ConfigurableABC:
    def build_from_conf(self, conf):
        raise NotImplementedError

    def save_to_conf(self):
        raise NotImplementedError

    @property
    def conf_fields(self):
        return NotImplemented


class LaneLayout(LayoutItem, ItemWithAnchors, ConfigurableABC):
    def __init__(self, name, offset: V3, length, width, rotate=0, vehicle_height=0, **kwargs):
        offset.iadd1("z", vehicle_height)
        super(LaneLayout, self).__init__(offset, V3(length, width, 0), rotate, **kwargs)
        self.name = name
        self.length = length
        self.width = width
        self.vehicle_height = vehicle_height


class CellLayout(LayoutItem):
    def __init__(self, idx: V3, offset: V3, rotate, **kwargs):
        super(CellLayout, self).__init__(offset, size=TEU.one(along=0), rotate=rotate, **kwargs)
        self.idx = idx


class LayoutHolder:
    def __init__(self,
                 V3 offset=V3.zero(),
                 V3 size=V3.one(),
                 double rotate=0,
                 **kwargs
                 ):
        self.layout = LayoutItem(offset, size, rotate, **kwargs)

    def move(self, V3 offset, double rotate=0):
        return (<LayoutItem> self.layout).move(offset, rotate)

    def transform_to(self, V3 coord, other=None):
        return (<LayoutItem> self.layout).transform_to(coord, other)

    def coord_l2g(self, V3 local_offset):
        return (<LayoutItem> self.layout).coord_l2g(local_offset)

    def coord_g2l(self, V3 global_offset):
        return (<LayoutItem> self.layout).coord_g2l(global_offset)

    def center_coord(self, transform_to=None):
        return (<LayoutItem> self.layout).center_coord(transform_to)

    def top_coord(self, transform_to=None):
        return (<LayoutItem> self.layout).top_coord(transform_to)

    def bottom_coord(self, transform_to=None):
        return (<LayoutItem> self.layout).bottom_coord(transform_to)

    def add_anchor(self, name, V3 coord):
        return (<LayoutItem> self.layout).add_anchor(name, coord)

    def get_anchor(self, name, transform_to=None):
        return (<LayoutItem> self.layout).get_anchor(name, transform_to)

    @property
    def offset(self):
        return (<LayoutItem> self.layout).offset

    @property
    def size(self):
        return (<LayoutItem> self.layout).size

    @size.setter
    def size(self, V3 value):
        (<LayoutItem> self.layout).size = value

    @property
    def rotate(self):
        return (<LayoutItem> self.layout).rotate


class BlockLayout(LayoutHolder, ItemWithAnchors, ConfigurableABC):
    def __init__(self, offset: V3, shape: V3, rotate=0, lanes=()):
        super(BlockLayout, self).__init__(offset, V3.zero(), rotate)
        self.lanes = {lane.name: lane for lane in lanes}
        self.shape = shape.as_V3i()
        self._cells = np.empty(self.shape.to_list(), dtype=object)

    def make_cell(self, idx: V3, local_offset):
        i, j, k = idx.as_ints()
        teu = TEU.one()
        offset = self.coord_l2g(local_offset)
        self._cells[i, j, k] = CellLayout(idx, offset, self.rotate)
        for i in range(3):
            self.size[i] = max(self.size[i], local_offset[i] + teu[i])

    def cell(self, cell_idx):
        i, j, k = cell_idx
        return self._cells[i, j, k]

    def cells(self):
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                for k in range(self.shape[2]):
                    yield self._cells[i, j, k]

    def lane(self, name):
        return self.lanes[name]

    def projected_coord_on_lane_from_cell_idx(self, lane, cell_idx, box_teu=1, transform_to=None):
        if not isinstance(lane, LaneLayout):
            lane = self.lane(lane)
        p0 = lane.transform_to(V3(0, lane.size.y / 2, lane.size.z / 2), self)
        vl = (lane.center_coord(transform_to=self) - p0).unit()
        bl = self.coord_from_cell_idx(cell_idx, box_teu) - p0
        p = min(max(bl.dot_product(vl), TEU.LENGTH * box_teu / 2), lane.length - TEU.LENGTH * box_teu / 2)
        v = lane.transform_to(V3(p, lane.size.y / 2, TEU.HEIGHT / 2), self)
        return self.layout.transform_to(v, transform_to)

    def next_cell(self, cell_idx):
        i, j, k = cell_idx
        return self._cells[i + 1, j, k]

    def coord_from_cell_idx(self, cell_idx, box_teu=1, transform_to=None):
        i, j, k = cell_idx
        if box_teu == 1:
            coord = self._cells[i, j, k].center_coord(transform_to=self)
        elif box_teu == 2:
            coord = (self._cells[i, j, k].center_coord(transform_to=self) + self.next_cell(cell_idx).center_coord(
                transform_to=self)) / 2
        else:
            raise NotImplementedError
        return self.layout.transform_to(coord, transform_to)


class EquipmentRangeLayout(LayoutHolder, ItemWithAnchors, ConfigurableABC):
    def __init__(self, offset, rotate=0, **kwargs):
        super(EquipmentRangeLayout, self).__init__(offset, V3.zero(), rotate, **kwargs)

# class LayoutSet:
#     def __init__(self):
#         self.items = {}
#         self.subset = {}
#
#     def add_item(self, V3 offset, V3 rotate, name, cls, *args, **kwargs):
#         self.items[name] = (offset, rotate, cls, args, kwargs)
#
#     def add_subset(self, V3 offset, V3 rotate, name, LayoutSet ls):
#         self.subset[name] = (offset, rotate, ls)
#
#     def __getitem__(self, item):
#         return self.subset[item][2]
#
#     def get_offset(self, name):
#         if name in self.subset:
#             return self.subset[name][0]
#         elif name in self.items:
#             return self.items[name][0]
#         else:
#             raise ValueError(name)
#
#     def get_rotation(self, name):
#         if name in self.subset:
#             return self.subset[name][0]
#         elif name in self.items:
#             return self.items[name][0]
#         else:
#             raise ValueError(name)
#
#     def freeze(self, V3 offset, V3 rotate=0):
#         for s_offset, s_rotate, ss in self.subset.values():
#             o = s_offset.l2g(offset, rotate)
#             r = s_rotate + rotate
#             yield from ss.freeze(o, r)
#         for i_offset, i_rotate, cls, args, kwargs in self.items.values():
#             o = i_offset.l2g(offset, rotate)
#             r = i_rotate + rotate
#             item = cls(*args, **kwargs)
#             item.move(o, r)
