from libc.stdint cimport int32_t

cdef int _axis_idx(name)

cdef class V3:
    cdef public double x
    cdef public double y
    cdef public double z

    cpdef V3 iadd1(V3 self, axis, double value)
    cpdef V3 isub1(V3 self, axis, double value)
    cpdef V3 imul1(V3 self, axis, double value)
    cpdef V3 iset1(V3 self, axis, double value)

    cpdef V3 rotate(V3 self, RotateOperator rtt_op, V3 ref=?)
    cpdef V3 rotate_angle(V3 self, double angle, V3 ref=?)
    cpdef double length(V3 self)
    cpdef double dot_product(V3 self, V3 other)

    cdef void cpy2mem_f(self, double* ptr)
    cdef void cpy2mem_i(self, int32_t* ptr)


cdef class V3i(V3):
    pass

cdef double _TEU_LENGTH
cdef double _TEU_WIDTH
cdef double _TEU_HEIGHT

cdef class RotateOperator:
    cdef readonly double angle
    cdef readonly double radian
    cdef readonly double sinv
    cdef readonly double cosv

