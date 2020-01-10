from libc.stdint cimport int32_t

cdef int _axis_idx(name)

cdef class V3:
    cdef public float x
    cdef public float y
    cdef public float z

    cpdef iadd1(V3 self, axis, float value)
    cpdef isub1(V3 self, axis, float value)
    cpdef imul1(V3 self, axis, float value)
    cpdef iset1(V3 self, axis, float value)

    cpdef rotate(V3 self, RotateOperator rtt_op, V3 ref=?)
    cpdef float length(V3 self)
    cpdef float dot_product(V3 self, V3 other)

    cdef cpy2mem_f(self, float* ptr)
    cdef cpy2mem_i(self, int32_t* ptr)


cdef class V3i(V3):
    pass

cdef float _TEU_LENGTH
cdef float _TEU_WIDTH
cdef float _TEU_HEIGHT

cdef class RotateOperator:
    cdef float angle
    cdef float radian
    cdef float sinv
    cdef float cosv

