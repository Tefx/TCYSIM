from copy import copy

from tcysim.framework.motion.component import Component
from tcysim.framework.equipment import Equipment
from tcysim.utils import V3, TEU


class Crane(Equipment):
    gantry: Component = NotImplemented
    trolley: Component = NotImplemented
    hoist: Component = NotImplemented
    between_clearance: float = 32.5 + 5
    height_clearance: float = 1

    def __init__(self, yard, block, init_offset, **attrs):
        components = self.gantry, self.trolley, self.hoist
        init_offset = init_offset if init_offset >= 0 else block.size.x - init_offset
        init_offset = V3(init_offset, 0, 0)
        super().__init__(yard, components, block.offset, block.size, block.rotate, init_offset, **attrs)
        self.gantry, self.trolley, self.hoist = self.components

    def box_equipment_shift(self):
        return V3.zero().add1(2, TEU.HEIGHT / 2)

    def check_interference(self, op):
        axis = self.gantry.axis
        p0 = op.paths[self.gantry]
        self_loc = self.local_coord()
        for other in self.nearby_equipments():
            if abs(self.local_coord().x - other.local_coord(self).x) < 32.5:
                print(self.time, self.local_coord().x, other.local_coord(self).x)
                print(self.state, other.state, op, other.current_op)
                raise Exception("cranes crash!")
            new_loc = other.local_coord(self)
            other_loc = copy(new_loc)
            if other_loc[axis] > self_loc[axis]:
                dis = other_loc[axis] - p0.max
                new_loc[axis] = p0.max + self.between_clearance + 1
            else:
                dis = p0.min - other_loc[axis]
                new_loc[axis] = p0.min - self.between_clearance - 1
            if other.state == self.STATE.WORKING:
                p1 = other.current_op.paths[other.gantry]
                shift = self.coord_g2l(other.offset)[axis]
                if p0.intersect_test(p1, self.between_clearance, shift):
                    return True, other, self.transform(other, new_loc)
            else:
                if dis < self.between_clearance:
                    return True, other, self.transform(other, new_loc)
        return False, None, None
