from enum import Enum, auto

from tcysim.utils.dispatcher import Dispatcher
from ..request import Request, ReqType as _ReqType


class ReqBuilder(Dispatcher):
    ReqType = _ReqType

    def __init__(self, block):
        super(ReqBuilder, self).__init__()
        self.block = block
        self.yard = block.yard

    def __call__(self, req_type, *args, **kwargs):
        return self.dispatch(req_type, "_", *args, **kwargs)

    @Dispatcher.on(ReqType.STORE)
    def gen_store_request(self, time, box, lane):
        request = Request(self.ReqType.STORE, time, box, lane=lane)
        request.link_signal("start_or_resume", self.on_store_start, request)
        request.link_signal("off_agv", self.on_store_off_agv, request)
        request.link_signal("in_block", self.on_store_in_block, request)
        request.link_signal("finish_or_fail", self.on_store_finish_or_fail, request)
        return request

    @Dispatcher.on(ReqType.RETRIEVE)
    def gen_retrieve_request(self, time, box, lane):
        request = Request(self.ReqType.RETRIEVE, time, box, lane=lane)
        request.link_signal("start_or_resume", self.on_retrieve_start, request)
        request.link_signal("off_block", self.on_retrieve_leaving_block, request)
        request.link_signal("on_agv", self.on_retrieve_on_agv, request)
        request.link_signal("finish_or_fail", self.on_retrieve_finish_or_fail, request)
        return request

    @Dispatcher.on(ReqType.ADJUST)
    def gen_adjust_request(self, time, equipment, new_loc, blocking_request):
        request = Request(self.ReqType.ADJUST, time,
                          equipment=equipment,
                          src_loc=equipment.local_coord(),
                          new_loc=new_loc,
                          blocking_request=blocking_request)
        request.link_signal("start_or_resume", self.on_adjust_start, request)
        request.link_signal("finish_or_fail", self.on_adjust_finish_or_fail, request)
        return request

    def on_store_start(self, time, request):
        self.yard.boxes.add(request.box)
        pass

    def on_store_finish_or_fail(self, time, request):
        pass

    def on_store_off_agv(self, time, request):
        box = request.box
        box.state = box.STATE_STORING
        request.sync(time)
        box.equipment = request.equipment

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
        box.state = request.box.STATE_RETRIEVING
        box.retrieve(time)
        box.block.release_stack(time, box.location)
        box.equipment = request.equipment

    def on_retrieve_on_agv(self, time, request):
        request.sync(time)
        box = request.box
        box.state = request.box.STATE_RETRIEVED
        box.equipment = None

    def on_adjust_start(self, time, request):
        blocking_req = request.blocking_request
        blocking_req.ready(time)
        blocking_req.equipment.job_scheduler.schedule(time)

    def on_adjust_finish_or_fail(self, time, request):
        pass

