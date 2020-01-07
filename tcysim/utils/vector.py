from copy import copy
from math import sin, cos, pi, sqrt, inf
from .math import feq

class V3:
    __slots__ = ["v", "dim"]

    @staticmethod
    def axis_idx(name):
        if isinstance(name, int):
            if name < 3:
                return name
            else:
                raise Exception("Error axis: {}".format(name))
        elif name == "x":
            return 0
        elif name == "y":
            return 1
        elif name == "z":
            return 2

    def __init__(self, *v):
        self.v = list(v)
        self.dim = len(v)

    def __getitem__(self, item):
        return self.v[self.axis_idx(item)]

    def __setitem__(self, key, value):
        self.v[self.axis_idx(key)] = value

    def __getattr__(self, item):
        idx = self.axis_idx(item)
        if idx is not None:
            return self.v[idx]
        else:
            return super(V3, self).__getattr__(item)

    def __setattr__(self, key, value):
        idx = self.axis_idx(key)
        if idx:
            self.v[idx] = value
            return self.v[idx]
        else:
            return super(V3, self).__setattr__(key, value)

    def __iter__(self):
        yield from self.v

    def __add__(self, other):
        if isinstance(other, V3):
            return V3(*(x + y for x, y in zip(self, other)))
        else:
            return V3(*(x + other for x in self))

    def __iadd__(self, other):
        if isinstance(other, V3):
            for i in range(self.dim):
                self[i] += other[i]
        else:
            for i in range(self.dim):
                self[i] += other
        return self

    def __sub__(self, other):
        if isinstance(other, V3):
            return V3(*(x - y for x, y in zip(self, other)))
        else:
            return V3(*(x - other for x in self))

    def __mul__(self, other):
        if isinstance(other, V3):
            return V3(*(x * y for x, y in zip(self, other)))
        else:
            return V3(*(x * other for x in self))

    def __truediv__(self, other):
        if isinstance(other, V3):
            return V3(*(x / y for x, y in zip(self, other)))
        else:
            return V3(*(x / other for x in self))

    def __floordiv__(self, other):
        if isinstance(other, V3):
            return V3(*(x // y for x, y in zip(self, other)))
        else:
            return V3(*(x // other for x in self))

    def __eq__(self, other):
        for i in range(self.dim):
            if not feq(self.v[i], other.v[i]):
                return False
        return True

    def __le__(self, other):
        return all(x < y for x, y in zip(self, other))

    def __ge__(self, other):
        return all(x > y for x, y in zip(self, other))

    def __copy__(self):
        return V3(*self)

    def __repr__(self):
        return "V({})".format(", ".join(map("{:.2f}".format, self)))

    def iadd1(self, axis, value):
        axis = self.axis_idx(axis)
        self[axis] += value
        return self

    def isub1(self, axis, value):
        axis = self.axis_idx(axis)
        self[axis] -= value
        return self

    def imul1(self, axis, value):
        axis = self.axis_idx(axis)
        self[axis] *= value
        return self

    def iset1(self, axis, value):
        axis = self.axis_idx(axis)
        self[axis] = value
        return self

    def add1(self, axis, value):
        return V3(*self).iadd1(axis, value)

    def sub1(self, axis, value):
        return V3(*self).isub1(axis, value)

    def mul1(self, axis, value):
        return V3(*self).imul1(axis, value)

    def set1(self, axis, value):
        return V3(*self).iset1(axis, value)

    def unit(self):
        l = self.length()
        return V3(*(x / l for x in self.v))

    def astype(self, t):
        return V3(*(t(x) for x in self.v))

    @classmethod
    def zero(cls):
        return cls(0, 0, 0)

    @classmethod
    def one(cls):
        return cls(1, 1, 1)

    @classmethod
    def inf(cls):
        return cls(inf, inf, inf)

    def to_list(self):
        return copy(self.v)

    def to_tuple(self):
        return tuple(self.v)

    def rotate(self, rtt_op, ref=None):
        if ref:
            return (self - ref).rotate(rtt_op) + ref
        else:
            x = self[0] * rtt_op.cosv - self[1] * rtt_op.sinv
            y = self[0] * rtt_op.sinv + self[1] * rtt_op.cosv
            return V3(x, y, self[2])

    def length(self):
        return sqrt(sum(x * x for x in self))

    def dot_product(self, other):
        return sum(x * y for x, y in zip(self, other))


class TEU(V3):
    LENGTH = 6.1
    WIDTH = 2.44
    HEIGHT = 2.59

    def __init__(self, x, y, z, along=0):
        along = V3.axis_idx(along)
        if along == 0:
            super(TEU, self).__init__(self.LENGTH * x, self.WIDTH * y, self.HEIGHT * z)
        elif along == 1:
            super(TEU, self).__init__(self.WIDTH * x, self.LENGTH * y, self.HEIGHT * z)
        else:
            raise NotImplementedError

    @classmethod
    def one(cls, along=0):
        return TEU(1, 1, 1, along=along)


class RotateOperator:
    def __init__(self, angle):
        self.angle = angle
        self.radian = angle / 180 * pi
        self.sinv = sin(self.radian)
        self.cosv = cos(self.radian)

    def __neg__(self):
        return self.__class__(-self.angle)
