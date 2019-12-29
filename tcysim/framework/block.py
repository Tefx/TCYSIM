from copy import deepcopy

from tcysim.framework.equipment import Equipment
from tcysim.libc import CBlock
from tcysim.utils import V3

from .box import Box
from .layout import BlockLayout
from .request import ReqBuilder


class Block(BlockLayout, CBlock):
    ReqBuilder = ReqBuilder

    def __init__(self, yard, offset, shape:V3, rotate, stacking_axis, sync_axes, lanes=()):
        sync_axes = tuple(V3.axis_idx(x) for x in sync_axes)
        stacking_axis = V3.axis_idx(stacking_axis)
        self.equipments = []
        self.yard = yard
        BlockLayout.__init__(self, offset, shape, rotate, lanes=lanes)
        CBlock.__init__(self, shape, stacking_axis=stacking_axis, sync_axes=sync_axes)
        self.req_builder = self.ReqBuilder(yard)
        self.lock_waiting_requests = {}

    def deploy(self, equipments):
        for equipment in equipments:
            self.equipments.append(equipment)
            equipment.assign_block(self)

    def box_coord(self, box:Box, equipment:Equipment):
        return self.cell_coord(box.location, equipment, box.teu)
    
    def access_coord(self, lane, box:Box, equipment:Equipment):
        return self.cell_coord_map_to_lane(lane, box.location, equipment, box.teu)

    def acquire_stack(self, time, acquirer, *positions):
        succeed = True
        for pos in positions:
            pos = pos.set1(self.stacking_axis, 0)
            if self.is_locked(pos):
                idx = self.stack_hash(pos)
                if idx not in self.lock_waiting_requests:
                    self.lock_waiting_requests[idx] = set()
                acquirer.on_acquire_fail(time, idx)
                self.lock_waiting_requests[idx].add(acquirer)
                succeed = False
        if succeed:
            for pos in positions:
                self.lock(pos)
                acquirer.on_acquire_success(time, pos)
        return succeed

    def release_stack(self, time, *positions):
        for pos in positions:
            pos = pos.set1(self.stacking_axis, 0)
            self.unlock(pos)
            idx = self.stack_hash(pos)
            if idx in self.lock_waiting_requests:
                for request in self.lock_waiting_requests[idx]:
                    request.on_resource_release(time, idx)
                del self.lock_waiting_requests[idx]
