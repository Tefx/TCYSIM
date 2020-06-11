from ..exception.handling import *
from tcysim.utils.dispatcher import Dispatcher
from abc import ABC, abstractmethod


class ReqHandlerBase(Dispatcher, ABC):
    def __init__(self, equipment):
        super(ReqHandlerBase, self).__init__()
        self.equipment = equipment
        self.yard = equipment.yard

    def handle(self, time, request):
        yield from self.dispatch(request.req_type.name, "_", time, request)

    def on_conflict(self, time, op):
        pass

    def on_reject(self, time, e):
        if isinstance(e, ROREquipmentConflictError):
            op = e.args[0]
            op.request.on_reject(time)
            self.on_conflict(time, op)
        elif isinstance(e, RORBoxBeingOperatedError):
            request = e.args[0]
            request.on_reject(time)
        else:
            raise NotImplementedError(e)

    @Dispatcher.on("STORE")
    @abstractmethod
    def on_request_store(self, time, request):
        raise NotImplementedError

    @Dispatcher.on("RETRIEVE")
    @abstractmethod
    def on_request_retrieve(self, time, request):
        raise NotImplementedError
