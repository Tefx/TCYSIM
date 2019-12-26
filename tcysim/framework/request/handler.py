from enum import Enum, auto

from tcysim.utils.dispatcher import Dispatcher
from .request import Request, ReqStatus
from tcysim.utils import TEU


class ReqHandler(Dispatcher):
    class ReqType(Enum):
        STORE = auto()
        RETRIEVE = auto()
        ADJUST = auto()

    def __init__(self, block):
        self.block = block
        super(ReqHandler, self).__init__()

    def handle(self, time, request):
        yield from self.dispatch(request.req_type, time, request)

    @Dispatcher.on(ReqType.STORE)
    def on_request_store(self, time, request):
        box = request.box
        if request.status != ReqStatus.RESUME:
            box.store(time)
            box.block.lock(box.location)
            op = request.equipment.OpBuilder.StoreOp(request)
            op.access_loc = self.block.access_coord(request.lane, request.box, request.equipment).add1("z", TEU.HEIGHT)
            op.container_loc = self.block.box_coord(request.box, request.equipment).add1("z", TEU.HEIGHT / 2)
        else:
            op = request.last_op
        # print("STORE", time, box, request.status)
        yield op

    @Dispatcher.on(ReqType.RETRIEVE)
    def on_request_retrieve(self, time, request):
        # request.box.state = request.box.STATE_RETRIEVING
        # print(request, request.status, request.last_op)
        box = request.box
        if request.status == ReqStatus.RESUME:
            if request.last_op.op_type == request.equipment.op_builder.OpType.RESHUFFLE:
                yield request.last_op
                yield from self.gen_reshuffle_operations(time, request)
                box.retrieve(time)
                box.block.lock(box.location)
                op = request.equipment.OpBuilder.RetrieveOp(request)
                op.access_loc = self.block.access_coord(request.lane, request.box, request.equipment).add1("z", TEU.HEIGHT)
                op.container_loc = self.block.box_coord(request.box, request.equipment).add1("z", TEU.HEIGHT / 2)
                yield op
            elif request.last_op.op_type == request.equipment.OpBuilder.OpType.RETRIEVE:
                yield request.last_op
            else:
                raise NotImplementedError
        else:
            yield from self.gen_reshuffle_operations(time, request)
            box.retrieve(time)
            box.block.lock(box.location)
            op = request.equipment.OpBuilder.RetrieveOp(request)
            op.access_loc = self.block.access_coord(request.lane, request.box, request.equipment).add1("z", TEU.HEIGHT)
            op.container_loc = self.block.box_coord(request.box, request.equipment).add1("z", TEU.HEIGHT / 2)
            # print(op.op_type.name)
            yield op

    @Dispatcher.on(ReqType.ADJUST)
    def on_request_adjust(self, time, request):
        op = request.equipment.OpBuilder.AdjustOp(request)
        op.dst_loc = request.new_loc
        yield op

    def validate(self, time, req):
        if req.status == ReqStatus.SENTBACK:
            return req.cb_time != time
        elif req.box:
            if req.req_type == self.ReqType.RETRIEVE and \
                    req.box.state < req.box.STATE_STORED:
                return False
            else:
                return not req.block.is_locked(req.box.location)
        return True

    @classmethod
    def StoreRequest(cls, time, box, lane):
        return Request(cls.ReqType.STORE, time, box, lane=lane)

    @classmethod
    def RetrieveRequest(cls, time, box, lane):
        return Request(cls.ReqType.RETRIEVE, time, box, lane=lane)

    @classmethod
    def AdjustRequest(cls, time, equipment, new_loc):
        return Request(cls.ReqType.ADJUST, time, equipment=equipment, new_loc=new_loc)

    def gen_reshuffle_operations(self, time, request):
        # Caution: may need to generate a compound operation
        box = request.box
        request.rsf_count = 0
        equipment = request.equipment
        yard = request.block.yard
        for above_box in box.box_above(self.block.stacking_axis):
            request.rsf_count += 1
            op = request.equipment.OpBuilder.ReshuffleOp(request, reset=False)
            op.src_loc = self.block.box_coord(above_box, equipment).add1("z", TEU.HEIGHT / 2)
            dst_loc = self.block.yard.smgr.slot_for_reshuffle(above_box)

            request.link_signal("reshuffle_pickup", yard.reshuffle_pickup, box=above_box, equipment=equipment,
                                dst_loc=dst_loc)
            request.link_signal("reshuffle_putdown", yard.reshuffle_putdown, box=above_box)

            # above_box.state = above_box.STATE_RESHUFFLING
            # above_box.previous_loc = above_box.location
            # print("Reshuffle", above_box, above_box.state, above_box.location, box.location, above_box.block.is_locked(above_box.location), box.block.is_locked(box.location))
            above_box.reshuffle(dst_loc)
            above_box.block.lock(above_box.previous_loc)
            above_box.block.lock(above_box.location)
            op.dst_loc = self.block.box_coord(above_box, equipment).add1("z", TEU.HEIGHT / 2)
            yield op
