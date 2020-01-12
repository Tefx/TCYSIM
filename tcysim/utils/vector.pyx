from libc.math cimport sin, cos, pi, sqrt
from .math import feq
cimport cython

cdef int _axis_idx(name):
    if name == "x":
        return 0
    elif name == "y":
        return 1
    elif name == "z":
        return 2
    else:
        return name

@cython.freelist(512)
cdef class V3:

    @staticmethod
    def axis_idx(name):
        return _axis_idx(name)

    def __init__(V3 self, float x, float y, float z):
        self.x = x
        self.y = y
        self.z = z

    def __getitem__(V3 self, int item):
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        elif item == 2:
            return self.z

    def __setitem__(V3 self, int key, float value):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        elif key == 2:
            self.z = value

    def __iter__(V3 self):
        yield self.x
        yield self.y
        yield self.z

    def __add__(V3 self, other):
        cdef V3 o
        cdef float f
        if isinstance(other, V3):
            o = other
            return V3(self.x + o.x, self.y + o.y, self.z + o.z)
        else:
            f = other
            return V3(self.x + f, self.y + f, self.z + f)

    def __iadd__(V3 self, other):
        cdef V3 o
        cdef float f
        if isinstance(other, V3):
            o = other
            self.x += o.x
            self.y += o.y
            self.z += o.z
        else:
            f = other
            self.x += f
            self.y += f
            self.z += f
        return self

    def __sub__(V3 self, other):
        cdef V3 o
        cdef float f
        if isinstance(other, V3):
            o = other
            return V3(self.x - o.x, self.y - o.y, self.z - o.z)
        else:
            f = other
            return V3(self.x - f, self.y - f, self.z - f)

    def __mul__(V3 self, other):
        cdef V3 o
        cdef float f
        if isinstance(other, V3):
            o = other
            return V3(self.x * o.x, self.y * o.y, self.z * o.z)
        else:
            f = other
            return V3(self.x * f, self.y * f, self.z * f)

    def __truediv__(V3 self, other):
        cdef V3 o
        cdef float f
        if isinstance(other, V3):
            o = other
            return V3(self.x / o.x, self.y / o.y, self.z / o.z)
        else:
            f = other
            return V3(self.x / f, self.y / f, self.z / f)

    def __floordiv__(V3 self, other):
        cdef V3 o
        cdef float f
        if isinstance(other, V3):
            o = other
            return V3(self.x // o.x, self.y // o.y, self.z // o.z)
        else:
            f = other
            return V3(self.x // f, self.y // f, self.z // f)

    def __eq__(V3 self, V3 other):
        return feq(self.x, other.x) and feq(self.y, other.y) and feq(self.z, other.z)

    def __le__(V3 self, V3 other):
        return self.x <= other.x and self.y <= other.y and self.z <= other.z

    def __ge__(V3 self, V3 other):
        return self.x >= other.x and self.y >= other.y and self.z >= other.z

    def __copy__(V3 self):
        return V3(self.x, self.y, self.z)

    def __repr__(V3 self):
        return "V({})".format(", ".join(map("{:.2f}".format, self)))

    cpdef iadd1(V3 self, axis, float value):
        cdef int axis_idx = _axis_idx(axis)
        if axis_idx == 0:
            self.x += value
        elif axis_idx == 1:
            self.y += value
        elif axis_idx == 2:
            self.z += value
        else:
            raise NotImplementedError
        return self

    cpdef isub1(V3 self, axis, float value):
        cdef int axis_idx = _axis_idx(axis)
        if axis_idx == 0:
            self.x -= value
        elif axis_idx == 1:
            self.y -= value
        elif axis_idx == 2:
            self.z -= value
        else:
            raise NotImplementedError
        return self

    cpdef imul1(V3 self, axis, float value):
        cdef int axis_idx = _axis_idx(axis)
        if axis_idx == 0:
            self.x *= value
        elif axis_idx == 1:
            self.y *= value
        elif axis_idx == 2:
            self.z *= value
        else:
            raise NotImplementedError
        return self

    cpdef iset1(V3 self, axis, float value):
        cdef int axis_idx = _axis_idx(axis)
        if axis_idx == 0:
            self.x = value
        elif axis_idx == 1:
            self.y = value
        elif axis_idx == 2:
            self.z = value
        else:
            raise NotImplementedError
        return self

    def add1(V3 self, axis, float value):
        return V3(self.x, self.y, self.z).iadd1(axis, value)

    def sub1(V3 self, axis, value):
        return V3(self.x, self.y, self.z).isub1(axis, value)

    def mul1(V3 self, axis, value):
        return V3(self.x, self.y, self.z).imul1(axis, value)

    def set1(V3 self, axis, value):
        return V3(self.x, self.y, self.z).iset1(axis, value)

    def unit(V3 self):
        cdef float l = self.length()
        return V3(self.x / l, self.y / l, self.z / l)

    # def astype(self, t):
    #     return t(self.x), t(self.y), t(self.z)
    #
    @classmethod
    def zero(cls):
        return cls(0, 0, 0)

    @classmethod
    def one(cls):
        return cls(1, 1, 1)

    def to_list(self):
        return [self.x, self.y, self.z]

    def to_tuple(self):
        return self.x, self.y, self.z

    cpdef rotate(V3 self, RotateOperator rtt_op, V3 ref=None):
        cdef float x, y

        if ref:
            return (self - ref).rotate(rtt_op) + ref
        else:
            x = self.x * rtt_op.cosv - self.y * rtt_op.sinv
            y = self.x * rtt_op.sinv + self.y * rtt_op.cosv
            return V3(x, y, self.z)

    cpdef float length(V3 self):
        return sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    cpdef float dot_product(V3 self, V3 other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    cdef cpy2mem_f(self, float* ptr):
        ptr[0] = <float>self.x
        ptr[1] = <float>self.y
        ptr[2] = <float>self.z

    cdef cpy2mem_i(V3 self, int32_t* ptr):
        ptr[0] = <int32_t>self.x
        ptr[1] = <int32_t>self.y
        ptr[2] = <int32_t>self.z

    def as_V3i(self):
        return V3i(<int32_t>self.x, <int32_t>self.y, <int32_t>self.z)

    def as_ints(self):
        return <int32_t>self.x, <int32_t>self.y, <int32_t>self.z

cdef class V3i(V3):
    def __getitem__(self, int item):
        if item == 0:
            return <int32_t>self.x
        elif item == 1:
            return <int32_t>self.y
        elif item == 2:
            return <int32_t>self.z

    def __copy__(self):
        return V3i(self.x, self.y, self.z)

    def __iter__(self):
        yield <int32_t>self.x
        yield <int32_t>self.y
        yield <int32_t>self.z

    def to_list(self):
        return [<int32_t>self.x, <int32_t>self.y, <int32_t>self.z]

    def to_tuple(self):
        return <int32_t>self.x, <int32_t>self.y, <int32_t>self.z

    def __repr__(self):
        return "Vi({})".format(", ".join(map("{:.0f}".format, self)))


_TEU_LENGTH = 6.1
_TEU_WIDTH = 2.44
_TEU_HEIGHT = 2.59

cdef class TEU(V3):
    LENGTH = _TEU_LENGTH
    WIDTH = _TEU_WIDTH
    HEIGHT = _TEU_HEIGHT

    def __init__(self, x, y, z, along=0):
        cdef int idx = V3.axis_idx(along)
        if idx == 0:
            super(TEU, self).__init__(_TEU_LENGTH * x, _TEU_WIDTH * y, _TEU_HEIGHT * z)
        elif idx == 1:
            super(TEU, self).__init__(_TEU_WIDTH * x, _TEU_LENGTH * y, _TEU_HEIGHT * z)
        else:
            raise NotImplementedError

    @classmethod
    def one(cls, along=0):
        return TEU(1, 1, 1, along=along)

cdef class RotateOperator:
    def __cinit__(self, float angle):
        self.angle = angle
        self.radian = angle / 180.0 * pi
        self.sinv = sin(self.radian)
        self.cosv = cos(self.radian)

    def __neg__(self):
        return RotateOperator(-self.angle)
