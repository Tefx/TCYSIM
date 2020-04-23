from ..exception.handling import *
from tcysim.utils.dispatcher import Dispatcher


class ReqHandler(Dispatcher):
    def __init__(self, equipment):
        super(ReqHandler, self).__init__()
        self.equipment = equipment
        self.yard = equipment.yard

    def handle(self, time, request):
        yield from self.dispatch(request.req_type.name, "_", time, request)

    @Dispatcher.on("STORE")
    def on_request_store(self, time, request):
        raise NotImplementedError

    @Dispatcher.on("RETRIEVE")
    def on_request_retrieve(self, time, request):
        raise NotImplementedError

    @Dispatcher.on("RELOCATE")
    def on_request_relocate(self, time, request):
        raise NotImplementedError

    @Dispatcher.on("ADJUST")
    def on_request_adjust(self, time, request):
        raise NotImplementedError

    def on_conflict(self, time, op):
        raise NotImplementedError

    def on_reject(self, time, e):
        if isinstance(e, ROREquipmentConflictError):
            op = e.args[0]
            op.request.on_reject(time)
            self.on_conflict(time, op)
        elif isinstance(e, RORAcquireFail):
            request = e.args[0]
            request.on_reject(time)
        elif isinstance(e, RORBoxBeingOperatedError):
            request = e.args[0]
            request.on_reject(time)
        elif isinstance(e, RORBoxHasUndoneRelocation):
            request = e.args[0]
            request.on_reject(time)
            if not request.one_time_attemp:
                self.yard.cmgr.add_callback(time + 60, request.ready)
        elif isinstance(e, RORNoPositionForRelocateError):
            request = e.args[0]
            request.on_reject(time)
            if not request.one_time_attemp:
                raise NotImplementedError(e) from e
        else:
            raise NotImplementedError(e)
