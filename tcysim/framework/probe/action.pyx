from pesim.pairing_heap cimport MinPairingHeapNode
from pesim.math_aux cimport time_eq, time_lt
from libc.stdint cimport uint64_t


cdef class ProbeActionTemplate:
    cdef readonly str probe_name
    cdef object func
    cdef object processor

    def __init__(self, str probe_name, func):
        self.probe_name = probe_name
        self.func = func
        self.processor = None

    def set_processor(self, processor):
        self.processor = processor

    def activate(self, double time, tuple args, dict kwargs, int reason):
        action = ProbeAction(self, time, args, kwargs, reason)
        self.processor.add_action(action)

    cdef call(self, tuple args, dict kwargs):
        self.func(self.processor, *args, **kwargs)

cdef uint64_t _global_idx = 0

cdef class ProbeAction(MinPairingHeapNode):
    cdef readonly double time
    cdef ProbeActionTemplate template
    cdef tuple args
    cdef dict kwargs
    cdef int reason
    cdef uint64_t idx

    def __init__(self, ProbeActionTemplate template, double time, tuple args, dict kwargs,
                 int reason):
        self.time = time
        self.template = template
        self.args = args
        self.kwargs = kwargs
        self.reason = reason
        self.idx = _global_idx + 1

        global _global_idx
        _global_idx += 1

    def __call__(self):
        self.template.call(self.args, self.kwargs)

    cpdef bint key_lt(self, MinPairingHeapNode other):
        if time_eq(self.time, (<ProbeAction>other).time):
            if self.reason == (<ProbeAction>other).reason:
                return self.idx < (<ProbeAction>other).idx
            else:
                return self.reason < (<ProbeAction>other).reason
        else:
            return time_lt(self.time, (<ProbeAction>other).time)
