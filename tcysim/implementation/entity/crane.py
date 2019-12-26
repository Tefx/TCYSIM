from copy import deepcopy, copy

from tcysim.framework.motion.component import Component
from tcysim.framework.equipment import Equipment
from tcysim.framework.operation import OpBuilder as OpBuilderBase
from tcysim.utils import V3


class Crane(Equipment):
    gantry: Component = NotImplemented
    trolley: Component = NotImplemented
    hoist: Component = NotImplemented
    clearance: float = 32.5

    class OpBuilder(OpBuilderBase):
        def move_steps(self, op, src_loc, dst_loc, load=False):
            hoist_mode = "rated load" if load else "no load"
            yield op.move(self.equipment.hoist, src_loc, self.equipment.hoist.max_height, hoist_mode)
            yield op.move(self.equipment.gantry, src_loc, dst_loc) | op.move(self.equipment.trolley, src_loc, dst_loc)
            yield op.move(self.equipment.hoist, self.equipment.hoist.max_height, dst_loc, hoist_mode)

        def adjust_steps(self, op, src_loc, dst_loc):
            dst_loc.z = self.equipment.hoist.max_height
            yield from self.move_steps(op, src_loc, dst_loc, load=False)

        def idle_steps(self, op, cur_loc):
            dst_loc = cur_loc.set1("z", self.equipment.hoist.max_height)
            yield from self.move_steps(op, cur_loc, dst_loc, load=False)

    def __init__(self, yard, block, init_offset, **attrs):
        components = self.gantry, self.trolley, self.hoist
        init_offset = init_offset if init_offset >= 0 else block.size.x - init_offset
        init_offset = V3(init_offset, 0, 0)
        super().__init__(yard, components, block.offset, block.size, block.rotate, init_offset, **attrs)
        self.gantry, self.trolley, self.hoist = self.components

    def check_interference(self, others, op):
        axis = self.gantry.axis
        p0 = op.paths[self.gantry]
        self_loc = self.local_coord()
        for other in others:
            if abs(self.local_coord().x - other.local_coord(self).x) < 32.5:
                print(self.time, self.local_coord().x, other.local_coord(self).x)
                exit(1)
            # print(self, other, self.state, other.state)
            new_loc = other.local_coord(self)
            other_loc = copy(new_loc)
            if other_loc[axis] > self_loc[axis]:
                dis = other_loc[axis] - p0.max
                new_loc[axis] = p0.max + self.clearance + 1
                # print("R", self_loc, other_loc, axis, p0.max, new_loc)
            else:
                dis = p0.min - other_loc[axis]
                new_loc[axis] = p0.min - self.clearance - 1
                # print("L", self_loc, other_loc, axis, p0.min, new_loc)
            if other.state == self.STATE.WORKING:
                p1 = other.current_op.paths[other.gantry]
                shift = self.coord_g2l(other.offset)[axis]
                # print("WRK", shift, self.clearance, p0.intersect_test(p1, self.clearance, shift),
                #       p0.min, p0.max, p1.min, p1.max)
                if p0.intersect_test(p1, self.clearance, shift):
                    return True, other, new_loc
            else:
                if dis < self.clearance:
                    return True, other, new_loc
        return False, None, None
