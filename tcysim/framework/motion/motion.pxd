cdef class Motion:
    cdef double start_v
    cdef double a
    cdef double start_time
    cdef double timespan, _orig_timespan
    cdef str mode
    cdef bint allow_interruption
    cdef bint orig

    cdef readonly double displacement
    cdef double finish_velocity
    cdef readonly double finish_time

    cdef Motion copy(self)
    cdef Motion split(self, double time)
    cdef void update(self)
    cdef double distance(self)
