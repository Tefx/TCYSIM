cdef float _EPSILON = 1e-3

EPSILON = _EPSILON

cpdef bint feq(float a, float b):
    return -_EPSILON <= a - b <= _EPSILON

