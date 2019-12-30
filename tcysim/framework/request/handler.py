from enum import Enum, auto

from ...utils.dispatcher import Dispatcher
from .request import ReqStatus
from .type import ReqType


class ReqHandler(Dispatcher):
    ReqType = ReqType

    def __init__(self, equipment):
        super(ReqHandler, self).__init__()
        self.equipment = equipment
        self.yard = equipment.yard

    def handle(self, time, request):
        yield from self.dispatch("handle", request.req_type, time, request)

    @Dispatcher.on("handle", ReqType.STORE)
    def on_request_store(self, time, request):
        if request.acquire_stack(time, request.box.location):
            yield self.equipment.OpBuilder.StoreOp(request)
        else:
            yield None

    @Dispatcher.on("handle", ReqType.RETRIEVE)
    def on_request_retrieve(self, time, request):
        yield from self.reshuffle_operations(time, request)
        if request.acquire_stack(time, request.box.location):
            yield self.equipment.op_builder.RetrieveOp(request)
        else:
            yield None

    def reshuffle_operations(self, time, request):
        box = request.box
        request.rsf_count = 0
        for above_box in box.box_above():
            new_loc = self.equipment.yard.smgr.slot_for_reshuffle(above_box)
            if request.acquire_stack(time, above_box.location, new_loc):
                yield self.gen_reshuffle_op(above_box, new_loc, request)
            else:
                yield None

    def gen_reshuffle_op(self, box, new_loc, original_request):
        original_request.rsf_count += 1
        original_request.link_signal("rsf_start_or_resume", self.on_reshuffle_start, box=box, dst_loc=new_loc)
        original_request.link_signal("rsf_pick_up", self.on_reshuffle_pickup, box=box, dst_loc=new_loc)
        original_request.link_signal("rsf_put_down", self.on_reshuffle_putdown, box=box, dst_loc=new_loc)
        original_request.link_signal("rsf_finish_or_fail", self.on_reshuffle_finish_or_fail, box=box, dst_loc=new_loc)
        return self.equipment.op_builder.ReshuffleOp(original_request, box, new_loc, reset=False)

    @Dispatcher.on("handle", ReqType.ADJUST)
    def on_request_adjust(self, time, request):
        yield self.equipment.OpBuilder.AdjustOp(request)

    def on_reject(self, time, request, last_op):
        request.on_reject(time)
        self.yard.tmgr.submit_request(time, request, ready=False)
        if last_op is None:
            pass
        if last_op.itf_other is not None:
            req_builder = last_op.itf_other.blocks[0].req_builder
            req2 = req_builder(req_builder.ReqType.ADJUST,
                               time, last_op.itf_other, last_op.itf_loc, blocking_request=request)
            self.yard.submit_request(time, req2)
        else:
            raise NotImplementedError

    def on_reshuffle_start(self, time, box, dst_loc):
        box.state = box.STATE_RESHUFFLING
        box.reshuffle_retrieve(time, dst_loc)
        pass

    def on_reshuffle_finish_or_fail(self, time, box, dst_loc):
        pass

    def on_reshuffle_pickup(self, time, box, dst_loc):
        box.equipment = self.equipment
        box.block.release_stack(time, box.location)

    def on_reshuffle_putdown(self, time, box, dst_loc):
        box.reshuffle_store(time)
        box.equipment = None
        box.block.release_stack(time, box.location)
