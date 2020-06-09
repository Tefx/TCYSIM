from enum import Enum, auto

from tcysim.framework import OperationBase


class OperationForCrane(OperationBase):
    class TYPE(Enum):
        STORE = auto()
        RETRIEVE = auto()
        RELOCATE = auto()
        ADJUST = auto()
        MOVE = auto()

    def __init__(self, type, request_or_equipment, box=None, locking_pos=(), **attrs):
        super(OperationForCrane, self).__init__(type, request_or_equipment, box, **attrs)
        self.locking_positions = list(locking_pos)

    def clean(self):
        self.locking_positions = None
        super(OperationForCrane, self).clean()

    def add_lock(self, pos):
        self.locking_positions.append(pos)

