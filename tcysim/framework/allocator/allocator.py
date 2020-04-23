class SpaceAllocator:
    def __init__(self, yard):
        self.yard = yard

    @property
    def time(self):
        return self.yard.env.time

    def available_blocks(self, box):
        return self.yard.blocks.values()

    def alloc_space(self, box, blocks, *args, **kwargs):
        raise NotImplementedError

    def slot_for_relocation(self, box, request, *args, **kwargs):
        raise NotImplementedError


