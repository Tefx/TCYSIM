from tcysim.utils.dispatcher import Dispatcher
from ..request import ReqType


class ReqHandler(Dispatcher):
    ReqType = ReqType

    def __init__(self, equipment):
        super(ReqHandler, self).__init__()
        self.equipment = equipment
        self.yard = equipment.yard

    def handle(self, time, request):
        yield from self.dispatch(request.req_type, "_", time, request)

    @Dispatcher.on(ReqType.STORE)
    def on_request_store(self, time, request):
        if request.acquire_stack(time, request.box.location):
            yield self.equipment.OpBuilder.StoreOp(request)
        else:
            yield None

    @Dispatcher.on(ReqType.RETRIEVE)
    def on_request_retrieve(self, time, request):
        yield from self.relocate_operations(time, request)
        if request.acquire_stack(time, request.box.location):
            yield self.equipment.op_builder.RetrieveOp(request)
        else:
            yield None

    def relocate_operations(self, time, request):
        box = request.box
        request.rsf_count = 0
        for above_box in box.box_above():
            new_loc = self.equipment.yard.smgr.slot_for_relocation(above_box)
            yield self.gen_relocate_op(time, above_box, new_loc, request)

    def gen_relocate_op(self, time, box, new_loc, original_request):
        if original_request.acquire_stack(time, box.location, new_loc):
            original_request.rsf_count += 1
            original_request.link_signal("rlct_start_or_resume", self.on_relocate_start, box=box, dst_loc=new_loc)
            original_request.link_signal("rlct_pick_up", self.on_relocate_pickup, box=box, dst_loc=new_loc)
            original_request.link_signal("rlct_put_down", self.on_relocate_putdown, box=box, dst_loc=new_loc)
            original_request.link_signal("rlct_finish_or_fail", self.on_relocate_finish_or_fail, box=box, dst_loc=new_loc)
            return self.equipment.op_builder.ReshuffleOp(original_request, box, new_loc, reset=False)

    @Dispatcher.on(ReqType.ADJUST)
    def on_request_adjust(self, time, request):
        yield self.equipment.OpBuilder.AdjustOp(request)

    def on_reject(self, time, request, last_op):
        request.on_reject(time)
        if last_op is None:
            pass
        elif last_op.itf_other is not None:
            req_builder = last_op.itf_other.blocks[0].req_builder
            req2 = req_builder(req_builder.ReqType.ADJUST,
                               time, last_op.itf_other, last_op.itf_loc, blocking_request=request)
            self.yard.submit_request(time, req2, ready=True)
        else:
            raise NotImplementedError

    def on_relocate_start(self, time, box, dst_loc):
        box.state = box.STATE_RESHUFFLING
        box.relocate_retrieve(time, dst_loc)
        pass

    def on_relocate_finish_or_fail(self, time, box, dst_loc):
        pass

    def on_relocate_pickup(self, time, box, dst_loc):
        box.equipment = self.equipment
        box.block.release_stack(time, box.previous_loc)

    def on_relocate_putdown(self, time, box, dst_loc):
        box.relocate_store(time)
        box.equipment = None
        box.block.release_stack(time, box.location)
