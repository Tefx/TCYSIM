from .define cimport *
from ..utils.vector cimport V3

cdef class CBlock:
    cdef Block c
    cpdef int count(self, int x=*, int y=*, int z=*, bint include_occupied=*)
    cpdef position_is_valid_for_size(self, V3 loc, teu)

