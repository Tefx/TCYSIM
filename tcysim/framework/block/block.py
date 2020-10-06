from itertools import product
from typing import Type

from tcysim.libc import CBlock
from tcysim.utils import V3, V3i

from ..layout import BlockLayout
from ..request import RequestBase, ReqDispatcher
from ..hash_salt import HashSalt


class Block(BlockLayout, CBlock):
    ReqCls: Type[RequestBase] = NotImplemented
    ReqDispatcherCls: Type[ReqDispatcher] = NotImplemented

    def __init__(self, yard, bid, offset, shape: V3, rotate, stacking_axis, sync_axes, lanes=()):
        self.id = bid
        sync_axes = tuple(V3.axis_idx(x) for x in sync_axes)
        stacking_axis = V3.axis_idx(stacking_axis)
        self.equipments = []
        self.yard = yard
        BlockLayout.__init__(self, offset, shape, rotate, lanes=lanes)
        CBlock.__init__(self, shape, stacking_axis=stacking_axis, sync_axes=sync_axes)
        self.req_dispatcher = self.ReqDispatcherCls(self)
        self.num_equipments = 0
        # self._hash = self.id
        self._hash = hash(HashSalt.Block + self.id)

    def deploy(self, equipments):
        for equipment in equipments:
            if equipment not in self.equipments:
                self.equipments.append(equipment)
                equipment.assign_block(self)
        self.num_equipments = len(self.equipments)

    def box_coord(self, box, transform_to=None):
        return self.coord_from_cell_idx(box.location, box.teu, transform_to)

    def access_coord(self, lane, box, transform_to=None):
        return self.projected_coord_on_lane_from_cell_idx(lane, box.location, box.teu, transform_to)

    def available_cells(self, box):
        for cell in self.cells():
            if self.position_is_valid_for_size(*cell.idx, box.teu):
                yield cell.idx

    def pending_requests(self):
        yield from self.req_dispatcher.pool.all_requests()
        for equipment in self.equipments:
            if equipment.next_task:
                yield equipment.next_task

    def current_tasks(self):
        for equipment in self.equipments:
            task = equipment.current_tasks()
            if task is not None:
                yield task

    @classmethod
    def new_request(cls, type, time, *args, ready=False, **kwargs):
        req = cls.ReqCls(cls.ReqCls.TYPE[type], time, *args, **kwargs)
        if ready:
            req.ready(time)
        return req

    def __repr__(self):
        return "<{}>#{}".format(self.__class__.__name__, self.id)

    def __hash__(self):
        return self._hash

