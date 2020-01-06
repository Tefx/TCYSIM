from .define cimport *
from .block cimport CBlock
from tcysim.utils import V3
from cpython cimport PyObject

cdef class CBoxState:
    INITIAL = BOX_STATE_INITIAL
    ALLOCATED = BOX_STATE_ALLOCATED
    STORING = BOX_STATE_STORING
    STORED = BOX_STATE_STORED
    RELOCATING = BOX_STATE_RELOCATING
    RETRIEVING = BOX_STATE_RETRIEVING
    RETRIEVED = BOX_STATE_RETRIEVED


cdef class CBox:
    cdef Box c
    cdef public object equipment

    def __cinit__(self, bytes box_id, int size=20):
        cdef BoxSize c_size
        if size == 20:
            c_size = BOX_SIZE_TWENTY
        elif size == 40:
            c_size = BOX_SIZE_FORTY
        else:
            raise NotImplementedError
        box_init(&self.c, box_id, c_size)
        self.c._self = <PyObject*> self
        self.equipment = None
        print(self.id, self.state)

    def __destroy__(self):
        box_destroy(&self.c)

    # def alloc(self, int time, block, loc):
    #     if loc:
    #         self.set_location(block, *loc)
    #         # print("ALLOC", self.id, self.location)
    #         box_alloc(&self.c, time)
    #         # print("/ALLOC", self.location)
    #         return True
    #     else:
    #         return False
    #
    # def realloc(self, int time, loc):
    #     if self.c._holder_or_origin:
    #         return
    #     cdef CellIdx new_loc[3];
    #     new_loc[:] = loc
    #     # print("realloc", self.id, self.location)
    #     box_realloc(&self.c, time, new_loc)
    #     # print("/realloc", self.id)
    #
    # def relocate_alloc(self, time, dst_loc):
    #     cdef CellIdx new_loc[3];
    #     new_loc[:] = dst_loc
    #     # print("rlct_alloc", self.id, self.location, dst_loc)
    #     box_relocate_alloc(&self.c, time, new_loc)
    #     # print("/rlct_alloc")

    def alloc2(self, time, block, loc):
        cdef CellIdx new_loc[3];
        if self.state == BOX_STATE_INITIAL:
            self.set_location(block, *loc)
            box_alloc(&self.c, time)
        elif self.state == BOX_STATE_ALLOCATED:
            if not self.c._holder_or_origin:
                new_loc[:] = loc
                box_realloc(&self.c, time, new_loc)
            else:
                raise Exception("triple alloc")
        elif self.state == BOX_STATE_STORED:
            if not self.c._holder_or_origin:
                new_loc[:] = loc
                box_relocate_alloc(&self.c, time, new_loc)
        else:
            print(self.state)
            raise NotImplementedError

    def store(self, int time):
        # print("STORE", self.id, self.location)
        box_store(&self.c, time)
        # print("/STORE", self.location)

    def retrieve(self, int time):
        # print("RETRIEVE", self.id, self.location)
        box_retrieve(&self.c, time)
        # print("/RETRIEVE")

    def relocate_retrieve(self, time):
        # print("rlct_retrieve", self.id, self.location)
        box_relocate_retrieve(&self.c, time)
        # print("/rlct_retrieve")

    def relocate_store(self, time):
        self.previous_loc = self.location
        # print("rlct_store", self.id, self.location)
        box_relocate_store(&self.c, time)
        # print("/rlct_store")

    @property
    def id(self):
        return self.c.id

    @property
    def alloc_time(self):
        return self.c.alloc_time

    @property
    def store_time(self):
        return self.c.store_time

    @property
    def retrieval_time(self):
        return self.c.retrieval_time

    @property
    def location(self):
        return V3(self.c.loc[0], self.c.loc[1], self.c.loc[2])

    @location.setter
    def location(self, loc):
        self.c.loc[:] = loc

    @property
    def state(self):
        return self.c.state

    @state.setter
    def state(self, state):
        self.c.state = state

    @property
    def size(self):
        if self.c.size == BOX_SIZE_TWENTY:
            return 20
        elif self.c.size == BOX_SIZE_FORTY:
            return 40
        else:
            raise NotImplementedError

    @property
    def teu(self):
        if self.c.size == BOX_SIZE_TWENTY:
            return 1
        elif self.c.size == BOX_SIZE_FORTY:
            return 2
        else:
            raise NotImplementedError

    @property
    def block(self):
        return <object> self.c.block._self

    @block.setter
    def block(self, CBlock block):
        self.c.block = &block.c

    def set_location(self, CBlock block, CellIdx x, CellIdx y, CellIdx z):
        self.c.block = &block.c
        self.c.loc[:] = x, y, z

    def store_position(self):
        cdef CellIdx loc[3]
        box_store_position(&self.c, loc)
        return V3(loc[0], loc[1], loc[2])

    def relocate_position(self, new_loc):
        cdef CellIdx loc[3]
        loc[:] = new_loc
        box_relocate_position(&self.c, loc)
        return V3(loc[0], loc[1], loc[2])

    def box_above(self):
        axis = self.block.stacking_axis
        if axis < 0:
            return
        while True:
            loc = self.location
            axis = V3.axis_idx(axis)
            # print("ABOVE", self.id, self.location)
            box = self.block.top_box(loc, axis)
            # print("/ABOVE")
            if box is self:
                break
            yield box

    def position_is_valid(self, CBlock block, CellIdx x, CellIdx y, CellIdx z):
        cdef CellIdx loc[3]
        loc[:] = x, y, z
        return box_position_is_valid(&self.c, &block.c, loc)

    def current_coord(self, equipment=None):
        return self.block.box_coord(self, equipment)

    def store_coord(self, equipment=None, loc=None):
        loc = loc or self.store_position()
        return self.block.cell_coord(loc, equipment, self.teu)

    def access_coord(self, lane, equipment=None):
        return self.block.access_coord(lane, self, equipment)

    def coord(self):
        if self.equipment:
            return self.equipment.coord_to_box()
        elif BOX_STATE_STORED <= self.state < BOX_STATE_RETRIEVING:
            if self.state == BOX_STATE_RELOCATING:
                return self.block.cell_coord(self.previous_loc, None, self.teu)
            return self.block.box_coord(self, None)

    def __repr__(self):
        return "Box[{}'|{}]".format(self.size, self.c.id.decode("utf-8"))

