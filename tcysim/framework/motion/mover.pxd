from collections import deque
from libc.math cimport sqrt, fabs

from .motion cimport Motion

cdef class Spec:
    cdef float v
    cdef float a
    cdef float d
    cdef float _cache_w0
    cdef float _cache_w1

cdef class Mover:
    cdef float curr_v
    cdef float curr_a
    cdef float _state_curr_v
    cdef float _state_curr_a
    cdef readonly object pending_motions
    cdef public float loc
    cdef float time
    cdef dict specs

    cdef perform_motion(self, Motion m)
    cdef bint idle(self)
    cpdef bint allow_interruption(self)
    cpdef commit_motions(self, motions)
    cdef create_motions(self, float start_time, float displacement, bint allow_interruption=?, mode=?)
