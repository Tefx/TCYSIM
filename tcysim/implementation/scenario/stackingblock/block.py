from copy import copy
from itertools import product

from tcysim.utils import V3, TEU
from tcysim.framework import Block
from tcysim.utils.vector import V3i


class StackingBlock(Block):
    def __init__(self, yard, offset, shape: V3, stacking_area_size: V3 = None, rotate=0, lanes=()):
        super(StackingBlock, self).__init__(yard, offset, shape, rotate, stacking_axis="z", sync_axes=("y", "z"),
                                            lanes=lanes)
        self.unit_base_size = TEU.one()
        size = TEU(*shape) if stacking_area_size is None else stacking_area_size
        self.stacking_interval = (size - shape * self.unit_base_size) / (shape - 1)
        self.unit_bound_size = self.unit_base_size + self.stacking_interval

        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                for k in range(self.shape[2]):
                    idx = V3i(i, j, k)
                    self.make_cell(idx, self.unit_bound_size * idx)

    @property
    def bays(self):
        return self.shape[0]

    @property
    def rows(self):
        return self.shape[1]

    @property
    def tiers(self):
        return self.shape[2]

    def in_stacking_area(self, global_coord):
        return global_coord in self

    def cell_idx_from_coord(self, local_coord):
        idx = (local_coord // self.unit_bound_size).as_V3i()
        for i in range(3):
            if idx[i] > self.shape[i]:
                idx[i] = self.shape[i]
            elif idx[i] < 0:
                idx[i] = -1
        return idx

    def stack_height(self, num):
        return self.unit_bound_size[self.stacking_axis] * num - self.stacking_interval[self.stacking_axis]

    def max_height_within(self, src_local_coord, dst_local_coord):
        if self.stacking_axis < 0:
            raise NotImplementedError

        idx_0 = copy(self.cell_idx_from_coord(src_local_coord))
        idx_1 = copy(self.cell_idx_from_coord(dst_local_coord))

        for i in range(3):
            if idx_0[i] > idx_1[i]:
                idx_0[i], idx_1[i] = idx_1[i], idx_0[i]

        idx_0[1] -= 1
        idx_1[1] += 1

        rs = [range(max(idx_0[i], 0), min(idx_1[i] + 1, self.shape[i])) for i in range(3)]
        rs[self.stacking_axis] = (-1,)

        h_max = max((self.count(*idx, include_occupied=False) for idx in product(*rs)), default=0)
        return self.stack_height(h_max)

    def bay_state(self, i):
        return self.column_state(V3i(i,0,0), 1)

    def bay_is_valid(self, box, i):
        if self.position_is_valid_for_size(V3(i, 0, 0), box.teu):
            max_num = self.rows * self.tiers - self.tiers
            return self.count(i, -1, -1) < max_num
        else:
            return False

    def available_cells(self, box, allow_new_bay=True):
        for i in range(self.bays):
            if box.state == box.STATE.STORED and box.location.x == i:
                bay_avail = True
            else:
                if not allow_new_bay and self.bay_state(i) == self.COLUMN_USAGE.FREE:
                    bay_avail = False
                else:
                    bay_avail = self.bay_is_valid(box, i)
            if bay_avail:
                for j in range(self.rows):
                    loc = V3i(i, j, self.count(i, j))
                    if box.position_is_valid(self, loc):
                        yield loc

    def zone_from_coord(self, local_coord):
        """
          (2,0) *    (2,1)    * (2,2)
        ********.-------------.********
          (1,0) |    (1,1)    | (1,2)
        ********.-------------.********
          (0,0) *    (0,1)    * (0,2)
        """
        if local_coord.x < 0:
            h = 0
        elif local_coord.x > self.size.x:
            h = 2
        else:
            h = 1
        if local_coord.y < 0:
            v = 0
        elif local_coord.y > self.size.y:
            v = 2
        else:
            v = 1
        return v, h
