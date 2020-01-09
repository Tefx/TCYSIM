from .mover import Mover
from tcysim.utils import V3


class Component(Mover):
    def __init__(self, axis, specs, trace=False, may_interfere=False, **other_spec):
        self.axis = V3.axis_idx(axis)
        self.may_interfere = may_interfere
        self.paths = None
        self.other_spec = other_spec
        self.specs = specs
        super(Component, self).__init__(specs)

    def __copy__(self):
        if self.__class__ is not Component:
            raise NotImplementedError
        return Component(self.axis, self.specs, self.paths is not None, self.may_interfere, **self.other_spec)

    def __getattr__(self, item):
        return self.other_spec[item]
