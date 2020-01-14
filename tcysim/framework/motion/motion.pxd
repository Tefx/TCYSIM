cdef class Motion:
    cdef double start_v
    cdef double a
    cdef double start_time
    cdef double timespan
    cdef bint allow_interruption

    cdef readonly double displacement
    cdef double finish_velocity
    cdef readonly double finish_time

    cdef Motion split(self, double time)
    cdef update(self)
