from libc.math cimport round

# cdef double _EPSILON = 1e-3
cdef double _EPSILON = 2.0 ** -16
cdef double _EPSILON_ROUND = _EPSILON

EPSILON = _EPSILON

cpdef bint feq(double a, double b):
    return -_EPSILON <= a - b <= _EPSILON

cpdef bint flt(double a, double b):
    return a > b + _EPSILON

cpdef double fround(double a):
    return round(a / _EPSILON_ROUND) * _EPSILON_ROUND

