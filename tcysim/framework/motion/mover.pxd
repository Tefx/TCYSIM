from .motion cimport Motion

cdef class Spec:
    cdef readonly double v
    cdef readonly double a
    cdef readonly double d
    cdef double _cache_w0
    cdef double _cache_w1

cdef class Mover:
    cdef readonly double curr_v
    cdef readonly double curr_a
    cdef double _state_curr_v
    cdef double _state_curr_a
    cdef double _state_curr_t
    cdef readonly object pending_motions
    cdef public double loc
    cdef readonly double time
    cdef dict specs

    cdef void perform_motion(self, Motion m)
    cdef bint idle(self)
    cpdef bint allow_interruption(self)
    cpdef void commit_motions(self, motions)
    cdef tuple create_motions(self, double start_time, double displacement, bint allow_interruption, mode=?)
