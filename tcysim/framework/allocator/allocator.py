from abc import ABC, abstractmethod

class SpaceAllocatorBase(ABC):
    def __init__(self, yard):
        self.yard = yard

    @property
    def time(self):
        return self.yard.env.time

    def available_blocks(self, box):
        return self.yard.blocks.values()

    @abstractmethod
    def alloc_space(self, box, blocks, *args, **kwargs):
        pass

    @abstractmethod
    def slot_for_relocation(self, box, request, *args, **kwargs):
        pass


