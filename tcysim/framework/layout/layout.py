from copy import deepcopy, copy
import numpy as np

from ...utils.vector import V3, TEU, RotateOperator


class _LayoutItem:
    def __init__(self,
                 offset: V3 = V3.zero(),
                 size: V3 = V3.one(),
                 rotate: float = 0,
                 **kwargs
                 ):
        self.offset = copy(offset)
        self.size = copy(size)
        self.rotate = rotate
        self.rtt_operator = RotateOperator(rotate)
        self.r_rtt_operator = RotateOperator(-rotate)

    def __mul__(self, num):
        return [deepcopy(self) for _ in range(num)]

    def __contains__(self, coord):
        coord = coord.rotate(self.r_rtt_operator, ref=self.offset)
        return self.offset <= coord <= self.offset + self.size

    def coord_l2g(self, local_offset):
        return (local_offset).rotate(self.rtt_operator) + self.offset

    def coord_g2l(self, global_offset):
        return (global_offset - self.offset).rotate(self.r_rtt_operator)

    @property
    def center(self):
        return self.coord_l2g(self.size / 2)

    @property
    def top(self):
        return self.center.add1(self.size.z / 2)

    @property
    def bottom(self):
        return self.center.sub1(self.size.z / 2)

    def transform(self, other, coord: V3):
        return other.coord_g2l(self.coord_l2g(coord))


class LaneLayout(_LayoutItem):
    def __init__(self, name, offset: V3, length, width, rotate=0, vehicle_height=0, **kwargs):
        offset.iadd1("z", vehicle_height)
        super(LaneLayout, self).__init__(offset, V3(length, width, 0), rotate, **kwargs)
        self.name = name
        self.length = length
        self.width = width
        self.vehicle_height = vehicle_height


class CellLayout(_LayoutItem):
    def __init__(self, idx: V3, offset: V3, rotate, **kwargs):
        super(CellLayout, self).__init__(offset, size=TEU.one(along=0), rotate=rotate, **kwargs)
        self.idx = idx


class BlockLayout(_LayoutItem):
    def __init__(self, offset: V3, shape: V3, rotate=0, lanes=()):
        super(BlockLayout, self).__init__(offset, V3.zero(), rotate)
        self.lanes = {lane.name: lane for lane in lanes}
        self.shape = shape.astype(int)
        self._cells = np.empty(list(self.shape), dtype=object)

    def make_cell(self, idx: V3, local_offset):
        i, j, k = idx
        teu = TEU.one()
        offset = self.coord_l2g(local_offset)
        self._cells[i, j, k] = CellLayout(idx, offset, self.rotate)
        for i in range(3):
            self.size[i] = max(self.size[i], local_offset[i] + teu[i])

    def cell(self, cell_idx):
        return self._cells[cell_idx]

    def lane(self, name):
        return self.lanes[name]

    def coord2cell(self, coord):
        for cell in self._cells:
            if coord in cell:
                return cell

    def coord2lane(self, coord):
        for lane in self.lanes:
            if coord in lane:
                return lane

    def cell_coord_map_to_lane(self, lane, cell_idx, equipment, box_teu=1):
        if not isinstance(lane, LaneLayout):
            lane = self.lane(lane)
        p0 = lane.coord_l2g(V3(0, lane.size.y / 2, lane.size.z / 2))
        vl = (lane.center - p0).unit()
        bl = self.cell_coord(cell_idx, None, box_teu) - p0
        p = min(max(bl.dot_product(vl), TEU.LENGTH * box_teu / 2), lane.length - TEU.LENGTH * box_teu / 2)
        if equipment:
            return lane.transform(equipment, V3(p, lane.size.y / 2, 0))
        else:
            return lane.coord_l2g(V3(p, lane.size.y / 2, 0))

    def next_cell(self, cell_idx):
        i, j, k =  cell_idx
        return self._cells[i+1, j, k]

    def cell_coord(self, cell_idx, equipment, box_teu=1):
        i, j, k = cell_idx
        if box_teu == 1:
            coord = self._cells[i, j, k].center
        elif box_teu == 2:
            coord = (self._cells[i, j, k].center + self.next_cell(cell_idx).center) / 2
        else:
            raise NotImplementedError
        if equipment:
            return equipment.coord_g2l(coord)
        else:
            return coord


class EquipmentRangeLayout(_LayoutItem):
    def __init__(self, offset, move_range, rotate=0, **kwargs):
        super(EquipmentRangeLayout, self).__init__(offset, move_range, rotate, **kwargs)
