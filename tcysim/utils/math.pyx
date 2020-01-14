cdef double _EPSILON = 1e-3

EPSILON = _EPSILON

cpdef bint feq(double a, double b):
    return -_EPSILON <= a - b <= _EPSILON

