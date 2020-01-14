from libc.stdint cimport int32_t

cdef int _axis_idx(name)

cdef class V3:
    cdef public double x
    cdef public double y
    cdef public double z

    cpdef iadd1(V3 self, axis, double value)
    cpdef isub1(V3 self, axis, double value)
    cpdef imul1(V3 self, axis, double value)
    cpdef iset1(V3 self, axis, double value)

    cpdef rotate(V3 self, RotateOperator rtt_op, V3 ref=?)
    cpdef double length(V3 self)
    cpdef double dot_product(V3 self, V3 other)

    cdef cpy2mem_f(self, double* ptr)
    cdef cpy2mem_i(self, int32_t* ptr)


cdef class V3i(V3):
    pass

cdef double _TEU_LENGTH
cdef double _TEU_WIDTH
cdef double _TEU_HEIGHT

cdef class RotateOperator:
    cdef double angle
    cdef double radian
    cdef double sinv
    cdef double cosv

