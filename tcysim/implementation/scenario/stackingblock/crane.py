from copy import copy

from tcysim.framework import Component, Equipment
from tcysim.utils import V3, TEU


class CraneForStackingBlock(Equipment):
    gantry: Component = NotImplemented
    trolley: Component = NotImplemented
    hoist: Component = NotImplemented
    clearance_between = 32.5
    clearance_above_box = 1

    _btw_clr_error = 5

    def __init__(self, yard, block, init_offset, **attrs):
        components = self.gantry, self.trolley, self.hoist
        init_offset = init_offset if init_offset >= 0 else block.size.x - init_offset
        init_offset = V3(init_offset, 0, 0)
        super().__init__(yard, components, block.offset, block.size, block.rotate, init_offset, **attrs)
        self.gantry, self.trolley, self.hoist = self.components

    def attached_box_coord(self, transform_to="g"):
        return self.current_coord(transform_to=transform_to).sub1("z", TEU.HEIGHT / 2)

    def op_coord_from_box_coord(self, local_coord, transform_to=None):
        return self.transform_to(local_coord.add1("z", TEU.HEIGHT / 2), transform_to)

    def prepare_coord_for_op_coord(self, local_coord, transform_to=None):
        return self.transform_to(local_coord.add1("z", self.clearance_above_box), transform_to)

    def check_interference(self, op):
        axis = self.gantry.axis
        p0 = op.paths[self.gantry]
        self_loc = self.current_coord()
        for other in self.nearby_equipments():
            other_loc = other.current_coord(transform_to=self)
            # print("check", self, other, self_loc, other_loc)
            if abs(self_loc.x - other_loc.x) < self.clearance_between:
                print(self.time, self_loc.x, other_loc.x)
                print(self.idx, other.idx, self.state, other.state, op, other.current_op)
                print(self, other)
                raise Exception("cranes crash!")
            new_loc = other_loc
            other_loc = copy(new_loc)
            if other_loc[axis] > self_loc[axis]:
                dis = other_loc[axis] - p0.max
                new_loc[axis] = p0.max + self.clearance_between + self._btw_clr_error + 1
            else:
                dis = p0.min - other_loc[axis]
                new_loc[axis] = p0.min - self.clearance_between - self._btw_clr_error - 1
            if other.state == self.STATE.WORKING:
                p1 = other.current_op.paths[other.gantry]
                shift = other.transform_to(V3.zero(), self)[axis]
                if p0.intersect_test(p1, self.clearance_between + self._btw_clr_error, shift):
                    return True, other, self.transform_to(new_loc, other)
            else:
                if dis < self.clearance_between + self._btw_clr_error:
                    return True, other, self.transform_to(new_loc, other)
        return False, None, None
