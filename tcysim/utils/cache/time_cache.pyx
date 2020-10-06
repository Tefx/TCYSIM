cdef class TimeCache:
    cdef object func
    cdef object _obj
    cdef double time

    def __init__(self, object func):
        self.func = func
        self._obj = None
        self.time = -1

    def __getitem__(self, double time):
        if time > self.time + 1e-4:
            self.time = time
            self._obj = self.func(time)
        return self._obj

    cpdef object get(self, double time):
        if time > self.time + 1e-4:
            self.time = time
            self._obj = self.func(time)
        return self._obj
