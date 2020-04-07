from tcysim.framework.equipment import ReqHandler as ReqHandlerBase
from tcysim.framework.exception.handling import *
from tcysim.utils.dispatcher import Dispatcher


class ReqHandler(ReqHandlerBase):
    def on_conflict(self, time, op):
        if not op.request.one_time_only:
            req2 = self.yard.new_request("ADJUST", time,
                           equipment=op.itf_other,
                           src_loc=op.itf_other.current_coord(),
                           new_loc=op.itf_loc,
                           blocking_request=op.request)
            self.yard.submit_request(time, req2, ready=True)

    @Dispatcher.on("STORE")
    def on_request_store(self, time, request):
        request.acquire_stack(time, request.box.location)
        request.link_signal("start_or_resume", self.on_store_start, request)
        request.link_signal("off_agv", self.on_store_off_agv, request)
        request.link_signal("in_block", self.on_store_in_block, request)
        request.link_signal("finish_or_fail", self.on_store_finish_or_fail, request)
        yield self.equipment.OpBuilder.StoreOp(request)

    @Dispatcher.on("RETRIEVE")
    def on_request_retrieve(self, time, request):
        yield from self.reshuffle_operations(time, request)
        box = request.box
        if box.state == box.STATE.RELOCATING:
            raise RORBoxBeingOperatedError(request)
        elif box.state != box.STATE.STORED:
            print(box, box.state)
        assert box.state == box.STATE.STORED
        request.acquire_stack(time, request.box.location)
        request.link_signal("start_or_resume", self.on_retrieve_start, request)
        request.link_signal("off_block", self.on_retrieve_leaving_block, request)
        request.link_signal("on_agv", self.on_retrieve_on_agv, request)
        request.link_signal("finish_or_fail", self.on_retrieve_finish_or_fail, request)
        yield self.equipment.op_builder.RetrieveOp(request)

    @Dispatcher.on("RELOCATE")
    def on_request_relocate(self, time, request):
        yield from self.reshuffle_operations(time, request)
        box = request.box
        new_loc = getattr(request, "new_loc", False)
        if not new_loc:
            new_loc = self.equipment.yard.smgr.slot_for_relocation(box)
            if not new_loc:
                self.yard.fire_probe("allocator.fail.relocate", box)
                raise RORUndefinedError("no slot for relocation")
        request.acquire_stack(time, box.location, new_loc)
        yield self.gen_relocate_op(time, box, new_loc, request)

    def gen_relocate_op(self, time, box, new_loc, request):
        request.link_signal("rlct_start_or_resume", self.on_relocate_start, box=box, dst_loc=new_loc)
        request.link_signal("rlct_pick_up", self.on_relocate_pickup, box=box)
        request.link_signal("rlct_put_down", self.on_relocate_putdown, box=box)
        request.link_signal("rlct_finish_or_fail", self.on_relocate_finish_or_fail, box=box)
        return self.equipment.op_builder.RelocateOp(request, box, new_loc)

    def reshuffle_operations(self, time, request):
        box = request.box
        request.rsf_count = 0
        for above_box in box.box_above():
            if above_box.has_undone_relocation():
                raise RORBoxHasUndoneRelocation(request)
            new_loc = self.equipment.yard.smgr.slot_for_relocation(above_box)
            if not new_loc:
                self.yard.fire_probe("allocator.fail.relocate", above_box)
                raise RORUndefinedError("no slot for relocation")
            request.acquire_stack(time, above_box.location, new_loc)
            yield self.gen_relocate_op(time, above_box, new_loc, request)

    @Dispatcher.on("ADJUST")
    def on_request_adjust(self, time, request):
        request.link_signal("start_or_resume", self.on_adjust_start, request)
        request.link_signal("finish_or_fail", self.on_adjust_finish_or_fail, request)
        yield self.equipment.OpBuilder.AdjustOp(request)

    def on_store_start(self, time, request):
        request.block.boxes.add(request.box)

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
        request.block.boxes.remove(request.box)

    def on_retrieve_leaving_block(self, time, request):
        box = request.box
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

    def on_relocate_finish_or_fail(self, time, box):
        pass

    def on_relocate_pickup(self, time, box):
        box.equipment = self.equipment
        box.retrieve(time)
        box.block.release_stack(time, box.location)

    def on_relocate_putdown(self, time, box):
        box.store(time)
        box.equipment = None
        box.block.release_stack(time, box.location)
