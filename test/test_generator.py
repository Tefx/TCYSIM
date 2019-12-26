import random

from tcysim.framework.box import Box
from tcysim.framework.generator import BoxGenerator
from tcysim.framework.yard import Yard
from tcysim.implementation.management.space import SimpleStackingBlockAllocator


class SimpleYard(Yard):
    SpaceAllocator = SimpleStackingBlockAllocator


class SimpleBoxGenerator(BoxGenerator):
    def next_time(self, time):
        return time + random.uniform(0, 30)

    def store_time(self, alloc_time):
        return alloc_time + random.uniform(10, 20)

    def retrieve_time(self, store_time):
        return store_time + random.uniform(100, 200)

    def new_box(self):
        return Box(str(self.time).encode("utf-8"), size=random.choice((20, 40)))


if __name__ == '__main__':
    yard = SimpleYard()
    yard.install_generator(SimpleBoxGenerator(0))
    yard.start()

    yard.run_until(1000)
