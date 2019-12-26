from tcysim.framework.equipment import Equipment
from tcysim.libc import CBlock
from tcysim.utils import V3

from .box import Box
from .layout import BlockLayout
from .request import ReqHandler


class Block(BlockLayout, CBlock):
    ReqHandler = ReqHandler

    def __init__(self, yard, offset, shape:V3, rotate, stacking_axis, sync_axes, lanes=()):
        sync_axes = tuple(V3.axis_idx(x) for x in sync_axes)
        stacking_axis = V3.axis_idx(stacking_axis)
        self.equipments = []
        self.yard = yard
        BlockLayout.__init__(self, offset, shape, rotate, lanes=lanes)
        CBlock.__init__(self, shape, stacking_axis=stacking_axis, sync_axes=sync_axes)
        self.req_handler = self.ReqHandler(self)

    def deploy(self, equipments):
        for equipment in equipments:
            self.equipments.append(equipment)
            equipment.assign_block(self)

    def handle_request(self, time, request):
        yield from self.req_handler.handle(time, request)

    def reshuffles_needed(self, time, box):
        if self.stacking_axis < 0:
            yield from []
        else:
            top_box = box.top_above(axis=self.stacking_axis)
            while top_box is not box:
                loc = self.yard.smgr.slot_for_reshuffle(top_box)
                yield box, loc
                
    def box_coord(self, box:Box, equipment:Equipment):
        return self.cell_coord(box.location, equipment, box.teu)
    
    def access_coord(self, lane, box:Box, equipment:Equipment):
        return self.cell_coord_map_to_lane(lane, box.location, equipment, box.teu)


