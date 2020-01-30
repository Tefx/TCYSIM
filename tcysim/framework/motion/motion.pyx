cimport cython


@cython.freelist(512)
cdef class Motion:
    def __cinit__(self, double start_time, double timespan, double v, double a, bint allow_interruption=False):
        self.start_v = v
        self.a = a
        self.start_time = start_time
        self.timespan = timespan
        self.allow_interruption = allow_interruption
        self.update()

    cdef Motion split(self, double time):
        cdef double t = time - self.start_time
        cdef Motion m = Motion(self.start_time, t, self.start_v, self.a, allow_interruption=self.allow_interruption)
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
            self.start_v, self.a, self.allow_interruption)
