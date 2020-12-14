from cython cimport freelist
from libc.math cimport fabs

@freelist(1024)
cdef class Motion:
    def __cinit__(self, double start_time, double timespan, double v, double a, str mode, bint allow_interruption):
        self.start_v = v
        self.a = a
        self.start_time = start_time
        self.timespan = self._orig_timespan = timespan
        self.allow_interruption = allow_interruption
        self.mode = mode
        self.orig = True
        self.update()

    cdef Motion copy(self):
        cdef Motion m = Motion.__new__(Motion, self.start_time, self.timespan, self.start_v, self.a, self.mode, self.allow_interruption)
        m.orig = False
        return m

    cdef Motion split(self, double time):
        cdef double t = time - self.start_time
        cdef Motion m = Motion.__new__(Motion, self.start_time, t, self.start_v, self.a, self.mode, self.allow_interruption)
        m.orig = False
        self.start_v += self.a * t
        self.timespan -= t
        self.start_time = time
        self.update()
        return m

    cdef void update(self):
        self.displacement = self.start_v * self.timespan + 0.5 * self.a * self.timespan * self.timespan
        self.finish_velocity = self.start_v + self.a * self.timespan
        self.finish_time = self.start_time + self.timespan

    def __repr__(self):
        return "[MTN]({:.3f}/{:.3f}/{:.3f}/{:.3f}[{}])".format(
            self.start_time, self.timespan,
            self.start_v, self.a, self.finish_velocity, self.finish_time, self.displacement,
            self.allow_interruption)

    cdef double distance(self):
        cdef double d = 0
        cdef double brake_t
        cdef double t = self.timespan
        cdef double v = self.start_v
        if v * self.a < 0:
            brake_t = - v / self.a
            if t > brake_t:
                d += fabs(0.5 * v * brake_t)
                t -= brake_t
                v = 0
        d += fabs(v * t + 0.5 * self.a * t * t)
        return d



