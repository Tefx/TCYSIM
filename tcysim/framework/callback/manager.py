from pesim import TIME_FOREVER, Process, MinPairingHeap
from .callback import CallBack
from ..event_reason import EventReason


class CallBackManager(Process):
    def __init__(self, yard):
        self.yard = yard
        self.queue = MinPairingHeap()
        super(CallBackManager, self).__init__(yard.env)

    def add(self, callback: CallBack):
        self.queue.push(callback)
        if self.queue.first() is callback:
            self.activate(callback.time, EventReason.CALLBACK)

    def add_callback(self, time, func, *args, **kwargs):
        cb = CallBack(func, *args, **kwargs)
        cb.time = time
        self.add(cb)

    def _wait(self):
        cb = self.queue.first()
        if cb:
            return cb.time, EventReason.CALLBACK
        else:
            return TIME_FOREVER, EventReason.LAST

    def _process(self):
        self.queue.pop()(self.time)
