from pesim.pairing_heap cimport MinPairingHeapNode


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

    def activate(self, double time, tuple args, dict kwargs):
        action = ProbeAction(self, time, args, kwargs)
        self.processor.add_action(action)

    cdef call(self, tuple args, dict kwargs):
        self.func(self.processor, *args, **kwargs)


cdef class ProbeAction(MinPairingHeapNode):
    cdef readonly double time
    cdef ProbeActionTemplate template
    cdef tuple args
    cdef dict kwargs

    def __init__(self, ProbeActionTemplate template, double time, tuple args, dict kwargs):
        self.time = time
        self.template = template
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        self.template.call(self.args, self.kwargs)

    cpdef bint key_lt(self, MinPairingHeapNode other):
        return self.time < (<ProbeAction>other).time
