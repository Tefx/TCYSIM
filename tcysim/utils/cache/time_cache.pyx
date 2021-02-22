from pesim.math_aux cimport time_lt

cdef class TimeCache:
    cdef object func
    cdef object _obj
    cdef double time

    def __init__(self, object func):
        self.func = func
        self._obj = None
        self.time = -1

    def __getitem__(self, double time):
        if time_lt(self.time, time):
            self.time = time
            self._obj = self.func(time)
        return self._obj

    cpdef object get(self, double time):
        if time_lt(self.time, time):
            self.time = time
            self._obj = self.func(time)
        return self._obj
