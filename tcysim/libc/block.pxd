from .define cimport *

cdef class CBlock:
    cdef Block c
    cpdef int count(self, int x=*, int y=*, int z=*, bint include_occupied=*)

