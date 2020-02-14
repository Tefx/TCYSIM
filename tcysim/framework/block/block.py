from itertools import product

from tcysim.libc import CBlock
from tcysim.utils import V3, V3i

from ..layout import BlockLayout
from ..scheduler import ReqDispatcher


class Block(BlockLayout, CBlock):
    ReqDispatcher = ReqDispatcher

    def __init__(self, yard, bid, offset, shape: V3, rotate, stacking_axis, sync_axes, lanes=()):
        self.id = bid
        sync_axes = tuple(V3.axis_idx(x) for x in sync_axes)
        stacking_axis = V3.axis_idx(stacking_axis)
        self.equipments = []
        self.yard = yard
        BlockLayout.__init__(self, offset, shape, rotate, lanes=lanes)
        CBlock.__init__(self, shape, stacking_axis=stacking_axis, sync_axes=sync_axes)
        self.req_dispatcher = self.ReqDispatcher(self)
        self.lock_waiting_requests = {}
        self.num_equipments= 0
        self.boxes = set()

    def deploy(self, equipments):
        for equipment in equipments:
            self.equipments.append(equipment)
            equipment.assign_block(self)
        self.num_equipments = len(self.equipments)

    def box_coord(self, box, transform_to=None):
        return self.coord_from_cell_idx(box.location, box.teu, transform_to)

    def access_coord(self, lane, box, transform_to=None):
        return self.projected_coord_on_lane_from_cell_idx(lane, box.location, box.teu, transform_to)

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

    def available_cells(self, box):
        for i, j, k in product(*self.shape):
            if self.position_is_valid_for_size(i, j, k, box.teu):
                return loc
