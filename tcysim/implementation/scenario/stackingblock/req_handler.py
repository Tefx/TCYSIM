from tcysim.framework import Request, ReqType
from tcysim.framework.exception.handling import RORUndefinedError
from tcysim.implementation.base.policy.req_handler import ReqHandler
from tcysim.utils.dispatcher import Dispatcher


class CooperativeTwinCraneReqHandler(ReqHandler):
    @Dispatcher.on(ReqType.RETRIEVE)
    def on_request_retrieve(self, time, request):
        if self.equipment.idx == 1 and request.lane.name < 5:
            yield from self.reshuffle_operations(time, request)
            request.coop_flag = True
            box = request.box
            start_bay = request.block.bays // 2 - 1
            dst_loc = self.yard.smgr.slot_for_relocation(box, start_bay=start_bay, finish_bay=0)
            if not dst_loc:
                raise RORUndefinedError("no slot for relocation")
            request.acquire_stack(time, box.location, dst_loc)
            yield self.gen_relocate_op(time, request.box, dst_loc, request, coop_flag=True)
        else:
            yield from super(CooperativeTwinCraneReqHandler, self).on_request_retrieve(self, time, request)

    @Dispatcher.on(ReqType.STORE)
    def on_request_store(self, time, request):
        box = request.box
        block = request.block
        if self.equipment.idx == 0 and box.location.x >= block.bays // 2:
            start_bay = request.block.bays // 2 - 1
            dst_loc = self.yard.smgr.slot_for_relocation(box, start_bay=start_bay, finish_bay=0)
            if not dst_loc:
                raise RORUndefinedError("no slot for relocation")
            request.acquire_stack(time, dst_loc)
            request.coop_flag = True
            request.dst_loc = dst_loc
            request.link_signal("start_or_resume", self.on_store_start, request)
            request.link_signal("off_agv", self.on_store_off_agv, request)
            request.link_signal("in_block", self.on_store_in_block, request)
            request.link_signal("finish_or_fail", self.on_store_finish_or_fail, request)
            yield self.equipment.OpBuilder.StoreOp(request)
        else:
            yield from super(CooperativeTwinCraneReqHandler, self).on_request_store(self, time, request)

    def gen_relocate_op(self, time, box, new_loc, request, coop_flag=False):
        request.link_signal("rlct_start_or_resume", self.on_relocate_start, box=box, dst_loc=new_loc)
        request.link_signal("rlct_pick_up", self.on_relocate_pickup, box=box)
        request.link_signal("rlct_put_down", self.on_relocate_putdown, box=box,
                            original_request=request if coop_flag else None)
        request.link_signal("rlct_finish_or_fail", self.on_relocate_finish_or_fail, box=box)
        return self.equipment.op_builder.RelocateOp(request, box, new_loc)

    def on_relocate_putdown(self, time, box, original_request=None):
        super(CooperativeTwinCraneReqHandler, self).on_relocate_putdown(time, box)
        if original_request:
            if original_request.req_type == ReqType.RETRIEVE and getattr(original_request, "ph2", True):
                req2 = Request(self.ReqType.RETRIEVE, time, box, lane=original_request.lane, coop_flag=True)
                self.yard.submit_request(time, req2)

    def on_store_start(self, time, request):
        if getattr(request, "coop_flag", False):
            box = request.box
            box.final_loc = box.location
            box.alloc(time, None, request.dst_loc)
        super(CooperativeTwinCraneReqHandler, self).on_store_start(time, request)

    def on_store_in_block(self, time, request):
        if getattr(request, "coop_flag", False):
            box = request.box
            req2 = Request(self.ReqType.RELOCATE, time, box, new_loc=box.final_loc, coop_flag=True)
            self.yard.submit_request(time, req2)
        super(CooperativeTwinCraneReqHandler, self).on_store_in_block(time, request)