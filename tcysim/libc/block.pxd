from .define cimport *
from ..utils.vector cimport V3

cdef class CBlock:
    cdef Block_TCY c
    cpdef int count(self, int x=*, int y=*, int z=*, bint include_occupied=*)
    cpdef bint position_is_valid_for_size(self, int x, int y, int z, int teu)
    cpdef SlotUsage_TCY column_state(self, int x, int y, int z, int axis)
    cpdef top_box(self, V3 loc, int along)

