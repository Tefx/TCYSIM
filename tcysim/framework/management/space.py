class SpaceAllocator:
    def __init__(self, yard):
        self.yard = yard

    def register_block(self, block):
        pass

    def available_blocks(self, box):
        return self.yard.blocks

    def alloc_space(self, box, blocks):
        raise NotImplementedError

    def slot_for_reshuffle(self, box):
        raise NotImplementedError


