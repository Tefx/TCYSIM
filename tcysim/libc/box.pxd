from .define cimport *
from .block cimport CBlock
from tcysim.utils.vector cimport V3, V3i
from cpython cimport PyObject

cdef class CBoxState:
    pass

cdef class CBox:
    cdef Box_TCY c
    cdef public object equipment

    cpdef V3i store_position(self, V3 new_loc=?)
    cpdef CBox top_box_above(self)
