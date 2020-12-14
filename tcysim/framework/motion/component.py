from .mover import Mover
from tcysim.utils import V3


class Component(Mover):
    def __init__(self, axis, specs, may_interfere=False, **other_spec):
        self.may_interfere = may_interfere
        self.other_spec = other_spec
        self.name = None
        super(Component, self).__init__(specs, V3.axis_idx(axis))

    def __copy__(self):
        if self.__class__ is not Component:
            raise NotImplementedError
        return Component(self.axis, self.specs, self.may_interfere, **self.other_spec)

    def __getattr__(self, item):
        return self.other_spec[item]
