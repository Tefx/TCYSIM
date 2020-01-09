cdef class Motion:
    cdef float start_v
    cdef float a
    cdef float start_time
    cdef float timespan
    cdef bint allow_interruption

    cdef readonly float displacement
    cdef float finish_velocity
    cdef readonly float finish_time

    cdef Motion split(self, float time)
    cdef update(self)
