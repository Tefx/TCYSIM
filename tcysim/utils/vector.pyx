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

@cython.freelist(10000)
cdef class V3:

    @staticmethod
    def axis_idx(name):
        return _axis_idx(name)

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __getitem__(self, int item):
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        elif item == 2:
            return self.z

    def __setitem__(self, int key, value):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        elif key == 2:
            self.z = value

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __add__(self, other):
        cdef V3 o
        if isinstance(other, V3):
            o = other
            return V3(self.x + o.x, self.y + o.y, self.z + o.z)
        else:
            return V3(self.x + other, self.y + other, self.z + other)

    def __iadd__(self, other):
        cdef V3 o
        if isinstance(other, V3):
            o = other
            self.x += o.x
            self.y += o.y
            self.z += o.z
        else:
            self.x += other
            self.y += other
            self.z += other
        return self

    def __sub__(self, other):
        cdef V3 o
        if isinstance(other, V3):
            o = other
            return V3(self.x - o.x, self.y - o.y, self.z - o.z)
        else:
            return V3(self.x - other, self.y - other, self.z - other)

    def __mul__(self, other):
        cdef V3 o
        if isinstance(other, V3):
            o = other
            return V3(self.x * o.x, self.y * o.y, self.z * o.z)
        else:
            return V3(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other):
        cdef V3 o
        if isinstance(other, V3):
            o = other
            return V3(self.x / o.x, self.y / o.y, self.z / o.z)
        else:
            return V3(self.x / other, self.y / other, self.z / other)

    def __floordiv__(self, other):
        cdef V3 o
        if isinstance(other, V3):
            o = other
            return V3(self.x // o.x, self.y // o.y, self.z // o.z)
        else:
            return V3(self.x // other, self.y // other, self.z // other)

    def __eq__(self, V3 other):
        return feq(self.x, other.x) and feq(self.y, other.y) and feq(self.z, other.z)

    def __le__(self, V3 other):
        return self.x <= other.x and self.y <= other.y and self.z <= other.z

    def __ge__(self, V3 other):
        return self.x >= other.x and self.y >= other.y and self.z >= other.z

    def __copy__(self):
        return V3(self.x, self.y, self.z)

    def __repr__(self):
        return "V({})".format(", ".join(map("{:.2f}".format, self)))

    cpdef iadd1(self, axis, value):
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

    cpdef isub1(self, axis, value):
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

    cpdef imul1(self, axis, value):
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

    cpdef iset1(self, axis, value):
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

    def add1(self, axis, value):
        return V3(self.x, self.y, self.z).iadd1(axis, value)

    def sub1(self, axis, value):
        return V3(self.x, self.y, self.z).isub1(axis, value)

    def mul1(self, axis, value):
        return V3(self.x, self.y, self.z).imul1(axis, value)

    def set1(self, axis, value):
        return V3(self.x, self.y, self.z).iset1(axis, value)

    def unit(self):
        cdef float l = self.length()
        return V3(self.x / l, self.y / l, self.z / l)

    def astype(self, t):
        return V3(t(self.x), t(self.y), t(self.z))

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

    cpdef rotate(self, RotateOperator rtt_op, V3 ref=None):
        cdef float x, y, _x, _y, _z

        if ref:
            return (self - ref).rotate(rtt_op) + ref
        else:
            _x = self.x
            _y = self.y
            _z = self.z
            x = _x * rtt_op.cosv - _y * rtt_op.sinv
            y = _x * rtt_op.sinv + _y * rtt_op.cosv
            return V3(x, y, self.z)

    cpdef float length(self):
        cdef float x = self.x
        cdef float y = self.y
        cdef float z = self.z
        return sqrt(x * x + y * y + z * z)

    cpdef float dot_product(self, V3 other):
        cdef float x1 = self.x
        cdef float y1 = self.y
        cdef float z1 = self.z
        cdef float x2 = other.x
        cdef float y2 = other.y
        cdef float z2 = other.z
        return x1 * x2 + y1 * y2 + z1 * z2

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
