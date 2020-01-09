cdef int _axis_idx(name)

cdef class V3:
    cdef public object x
    cdef public object y
    cdef public object z

    cpdef iadd1(self, axis, value)
    cpdef isub1(self, axis, value)
    cpdef imul1(self, axis, value)
    cpdef iset1(self, axis, value)

    cpdef rotate(self, RotateOperator rtt_op, V3 ref=?)
    cpdef float length(self)
    cpdef float dot_product(self, V3 other)

cdef float _TEU_LENGTH
cdef float _TEU_WIDTH
cdef float _TEU_HEIGHT

cdef class RotateOperator:
    cdef float angle
    cdef float radian
    cdef float sinv
    cdef float cosv

