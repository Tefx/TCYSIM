from pesim import TIME_FOREVER, Process, MinPairingHeap
from .callback import CallBack
from ..priority import Priority


class CallBackManager(Process):
    def __init__(self, yard):
        self.yard = yard
        self.queue = MinPairingHeap()
        super(CallBackManager, self).__init__(yard.env)

    def add(self, callback: CallBack):
        self.queue.push(callback)
        if self.queue.first() is callback:
            self.activate(callback.time, Priority.CALLBACK)

    def add_callback(self, time, func, *args, **kwargs):
        cb = CallBack(func, *args, **kwargs)
        cb.time = time
        self.add(cb)

    def _wait(self, priority=Priority.CALLBACK):
        cb = self.queue.first()
        if cb:
            return cb.time, Priority.CALLBACK
        else:
            return TIME_FOREVER, Priority.FOREVER

    def _process(self):
        callback = self.queue.pop()
        self.yard.fire_probe(self.time, "callback.before", callback)
        callback(self.time)
        self.yard.fire_probe(self.time, "callback.after", callback)
