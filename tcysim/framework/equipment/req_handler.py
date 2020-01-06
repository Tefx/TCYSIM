from tcysim.utils.dispatcher import Dispatcher
from ..request import Request, ReqType


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
            request.link_signal("start_or_resume", self.on_store_start, request)
            request.link_signal("off_agv", self.on_store_off_agv, request)
            request.link_signal("in_block", self.on_store_in_block, request)
            request.link_signal("finish_or_fail", self.on_store_finish_or_fail, request)
            yield self.equipment.OpBuilder.StoreOp(request)
        else:
            yield None

    @Dispatcher.on(ReqType.RETRIEVE)
    def on_request_retrieve(self, time, request):
        yield from self.reshuffle_operations(time, request)
        if request.acquire_stack(time, request.box.location):
            request.link_signal("start_or_resume", self.on_retrieve_start, request)
            request.link_signal("off_block", self.on_retrieve_leaving_block, request)
            request.link_signal("on_agv", self.on_retrieve_on_agv, request)
            request.link_signal("finish_or_fail", self.on_retrieve_finish_or_fail, request)
            yield self.equipment.op_builder.RetrieveOp(request)
        else:
            yield None

    @Dispatcher.on(ReqType.RELOCATE)
    def on_request_relocate(self, time, request):
        yield from self.reshuffle_operations(time, request)
        box = request.box
        if request.acquire_stack(time, box.location, request.new_loc):
            yield self.gen_relocate_op(time, box, request.new_loc, request, reset=True)
        else:
            yield None

    def gen_relocate_op(self, time, box, new_loc, request, reset):
        request.link_signal("rlct_start_or_resume", self.on_relocate_start, box=box, dst_loc=new_loc)
        request.link_signal("rlct_pick_up", self.on_relocate_pickup, box=box, dst_loc=new_loc)
        request.link_signal("rlct_put_down", self.on_relocate_putdown, box=box, dst_loc=new_loc)
        request.link_signal("rlct_finish_or_fail", self.on_relocate_finish_or_fail, box=box, dst_loc=new_loc)
        return self.equipment.op_builder.RelocateOp(request, box, new_loc, reset=reset)

    def reshuffle_operations(self, time, request):
        box = request.box
        if box.state != box.STATE.STORED:
            yield None
        request.rsf_count = 0
        for above_box in box.box_above():
            new_loc = self.equipment.yard.smgr.slot_for_relocation(above_box)
            assert new_loc
            if request.acquire_stack(time, above_box.location, new_loc):
                yield self.gen_relocate_op(time, above_box, new_loc, request, reset=False)
            else:
                yield None

    @Dispatcher.on(ReqType.ADJUST)
    def on_request_adjust(self, time, request):
        request.link_signal("start_or_resume", self.on_adjust_start, request)
        request.link_signal("finish_or_fail", self.on_adjust_finish_or_fail, request)
        yield self.equipment.OpBuilder.AdjustOp(request)

    def on_reject(self, time, request, last_op):
        request.on_reject(time)
        if last_op is None:
            pass
        elif last_op.itf_other is not None:
            req2 = Request(self.ReqType.ADJUST, time,
                           equipment=last_op.itf_other,
                           src_loc=last_op.itf_other.local_coord(),
                           new_loc=last_op.itf_loc,
                           blocking_request=request)
            self.yard.submit_request(time, req2, ready=True)
        else:
            raise NotImplementedError

    def on_store_start(self, time, request):
        self.yard.boxes.add(request.box)
        pass

    def on_store_finish_or_fail(self, time, request):
        pass

    def on_store_off_agv(self, time, request):
        box = request.box
        box.start_store()
        box.equipment = request.equipment
        request.sync(time)

    def on_store_in_block(self, time, request):
        box = request.box
        box.store(time)
        box.block.release_stack(time, box.location)
        box.equipment = None

    def on_retrieve_start(self, time, request):
        pass

    def on_retrieve_finish_or_fail(self, time, request):
        self.yard.boxes.remove(request.box)

    def on_retrieve_leaving_block(self, time, request):
        box = request.box
        # box.retrieve(time)
        box.retrieve(time)
        box.equipment = request.equipment
        box.block.release_stack(time, box.location)

    def on_retrieve_on_agv(self, time, request):
        box = request.box
        box.finish_retrieve()
        box.equipment = None
        request.sync(time)

    def on_adjust_start(self, time, request):
        blocking_req = request.blocking_request
        blocking_req.ready(time)
        blocking_req.equipment.job_scheduler.schedule(time)

    def on_adjust_finish_or_fail(self, time, request):
        pass

    def on_relocate_start(self, time, box, dst_loc):
        box.alloc(time, None, dst_loc)

    def on_relocate_finish_or_fail(self, time, box, dst_loc):
        pass

    def on_relocate_pickup(self, time, box, dst_loc):
        box.equipment = self.equipment
        box.retrieve(time)
        box.block.release_stack(time, box.location)

    def on_relocate_putdown(self, time, box, dst_loc):
        box.store(time)
        box.equipment = None
        box.block.release_stack(time, box.location)
