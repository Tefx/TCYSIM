from ..exception.handling import *
from ..request import Request, ReqType as _ReqType
from tcysim.utils.dispatcher import Dispatcher


class ReqHandler(Dispatcher):
    ReqType = _ReqType

    def __init__(self, equipment):
        super(ReqHandler, self).__init__()
        self.equipment = equipment
        self.yard = equipment.yard

    def handle(self, time, request):
        yield from self.dispatch(request.req_type, "_", time, request)

    @Dispatcher.on(ReqType.STORE)
    def on_request_store(self, time, request):
        raise NotImplementedError

    @Dispatcher.on(ReqType.RETRIEVE)
    def on_request_retrieve(self, time, request):
        raise NotImplementedError

    @Dispatcher.on(ReqType.RELOCATE)
    def on_request_relocate(self, time, request):
        raise NotImplementedError

    @Dispatcher.on(ReqType.ADJUST)
    def on_request_adjust(self, time, request):
        raise NotImplementedError

    def on_reject(self, time, e):
        if isinstance(e, ROREquipmentConflictError):
            op = e.args[0]
            op.request.on_reject(time)
            req2 = Request(self.ReqType.ADJUST, time,
                           equipment=op.itf_other,
                           src_loc=op.itf_other.current_coord(),
                           new_loc=op.itf_loc,
                           blocking_request=op.request)
            self.yard.submit_request(time, req2, ready=True)
        elif isinstance(e, RORAcquireFail):
            request = e.args[0]
            request.on_reject(time)
        elif isinstance(e, RORBoxBeingOperatedError):
            request = e.args[0]
            request.on_reject(time)
        elif isinstance(e, RORBoxHasUndoneRelocation):
            request = e.args[0]
            request.on_reject(time)
            self.yard.cmgr.add_callback(time + 60, request.ready)
        else:
            raise NotImplementedError(e)

