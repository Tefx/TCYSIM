from copy import deepcopy, copy
import numpy as np
from collections import OrderedDict

from ...utils import V3, TEU, RotateOperator


class LayoutItem:
    def __init__(self,
                 offset: V3 = V3.zero(),
                 size: V3 = V3.one(),
                 rotate=0,
                 **kwargs
                 ):
        self.offset = copy(offset)
        self.size = copy(size)
        self.rotate = rotate
        self.rtt_operator = RotateOperator(rotate)
        self.r_rtt_operator = RotateOperator(-rotate)

    def __mul__(self, num):
        return [deepcopy(self) for _ in range(num)]

    # def __contains__(self, local_coord):
    #     return V3.zero() <= local_coord <= self.size

    def coord_l2g(self, local_offset):
        return local_offset.rotate(self.rtt_operator) + self.offset

    def coord_g2l(self, global_offset):
        return (global_offset - self.offset).rotate(self.r_rtt_operator)

    def center_coord(self, transform_to=None):
        return self.transform_to(self.size / 2, transform_to)

    def top_coord(self, transform_to=None):
        return self.transform_to((self.size / 2).add1("z", self.size.z / 2), transform_to)

    def bottom_coord(self, transform_to=None):
        return self.transform_to((self.size / 2).sub1("z", self.size.z / 2), transform_to)

    def transform_to(self, coord: V3, other=None):
        if other is None:
            return coord
        elif other == "g":
            return self.coord_l2g(coord)
        else:
            return other.coord_g2l(self.coord_l2g(coord))


class LaneLayout(LayoutItem):
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


class BlockLayout(LayoutItem):
    def __init__(self, offset: V3, shape: V3, rotate=0, lanes=()):
        super(BlockLayout, self).__init__(offset, V3.zero(), rotate)
        self.lanes = {lane.name: lane for lane in lanes}
        # self.shape = shape.astype(int)
        # self._cells = np.empty(list(self.shape), dtype=object)
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
        v = lane.transform_to(V3(p, lane.size.y / 2, lane.size.z / 2 + TEU.HEIGHT / 2), self)
        return self.transform_to(v, transform_to)

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
        return self.transform_to(coord, transform_to)


class EquipmentRangeLayout(LayoutItem):
    def __init__(self, offset, move_range, rotate=0, **kwargs):
        super(EquipmentRangeLayout, self).__init__(offset, move_range, rotate, **kwargs)
