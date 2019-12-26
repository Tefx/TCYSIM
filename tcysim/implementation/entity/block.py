from itertools import product

from tcysim.utils import V3, TEU
from tcysim.framework.block import Block


class StackingBlock(Block):
    def __init__(self, yard, offset, shape:V3, stacking_area_size:V3=None, rotate=0, lanes=()):
        super(StackingBlock, self).__init__(yard, offset, shape, rotate, stacking_axis="z", sync_axes=("y", "z"), lanes=lanes)

        self.unit_base_size = TEU.one()
        size = TEU(*shape) if stacking_area_size is None else stacking_area_size
        self.stacking_interval = (size - shape * self.unit_base_size) / (shape - 1)
        self.unit_bound_size = self.unit_base_size + self.stacking_interval

        for i in range(shape[0]):
            for j in range(shape[1]):
                for k in range(shape[2]):
                    idx = V3(i, j, k)
                    self.make_cell(idx, self.unit_bound_size * idx)

    @property
    def rows(self):
        return self.shape[0]

    @property
    def bays(self):
        return self.shape[1]

    @property
    def tiers(self):
        return self.shape[2]

    def in_stacking_area(self, coord):
        return coord in self

    def coord2cell(self, coord):
        idx = (self.coord_g2l(coord) // self.unit_bound_size).astype(int)
        return self.cell(idx)

    def stack_height(self, num):
        return self.unit_bound_size[self.stacking_axis] * num - self.stacking_interval[self.stacking_axis]

    def max_height_within(self, src_loc, dst_loc):
        if self.stacking_axis < 0:
            raise NotImplementedError

        h_max = 0
        idx_0 = self.coord2cell(src_loc).idx
        idx_1 = self.coord2cell(dst_loc).idx

        for i in range(3):
            if idx_0[i] > idx_1[i]: idx_0[i], idx_1[i] = idx_1[i], idx_0[i]

        idx_0[self.stacking_axis] = idx_1[self.stacking_axis] = -1
        rx = range(max(idx_0[0],0), min(idx_1[0], self.shape[0])+1)
        ry = range(max(idx_0[1],0), min(idx_1[1], self.shape[1])+1)
        rz = range(max(idx_0[2],0), min(idx_1[2], self.shape[2])+1)
        for idx_x, idx_y, idx_z in product(rx, ry, rz):
            h = self.count(idx_x, idx_y, idx_z, include_occupied=False)
            if h > h_max: h_max = h

        return self.stack_height(h_max)
