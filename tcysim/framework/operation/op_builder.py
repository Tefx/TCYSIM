from abc import ABC, abstractmethod
from typing import Type
from tcysim.utils.dispatcher import Dispatcher
from .operation import OperationBase


class OpBuilderBase(Dispatcher, ABC):
    OpCls: Type[OperationBase] = NotImplemented

    def __init__(self, equipment):
        self.equipment = equipment
        super(OpBuilderBase, self).__init__()

    @classmethod
    def new_Op(cls, type, *args, **kwargs):
        return cls.OpCls(cls.OpCls.TYPE[type], *args, **kwargs)

    @abstractmethod
    def move_steps(self, op, src_loc, dst_loc, load=False):
        pass
