from .define cimport *
from .block cimport CBlock
from tcysim.utils import V3
from cpython cimport PyObject


cdef class CBox:
    cdef Box c
    cdef public object equipment
    cdef public object previous_loc

    STATE_INITIAL = BOX_STATE_INITIAL
    STATE_ALLOCATED = BOX_STATE_ALLOCATED
    STATE_STORING = BOX_STATE_STORING
    STATE_STORED = BOX_STATE_STORED
    STATE_RESHUFFLING = BOX_STATE_RESHUFFLING
    STATE_RETRIEVING = BOX_STATE_RETRIEVING
    STATE_RETRIEVED = BOX_STATE_RETRIEVED

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

    def __destroy__(self):
        box_destroy(&self.c)

    def alloc(self, int time):
        # print("Alloc", self.location)
        box_alloc(&self.c, time)
        # print("Alloc Done")

    def store(self, int time):
        # print("Store")
        box_store(&self.c, time)
        # print("Store Done", self.id, self.location)

    def retrieve(self, int time):
        # print("Retrieve", time, self.id, self.location)
        box_retrieve(&self.c, time)
        # print("Retrieve Done")

    def reshuffle(self, dst_loc):
        # print("RSF", self.id, self.location, dst_loc)
        cdef CellIdx new_loc[3];
        new_loc[:] = dst_loc
        self.previous_loc = self.location
        box_reshuffle(&self.c, new_loc)
        # print("RSF Done", self.id, self.location)

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

    def box_above(self, int axis):
        while True:
            loc = self.location
            axis = V3.axis_idx(axis)
            # print("ABOVE", self, loc, self.state, self.block)
            box = self.block.top_box(loc, axis)
            # print("ABOVE DONE", box, box.location, box.state)
            assert loc[0] == box.location[0] and loc[1] == box.location[1]
            if box is self:
                break
            yield box

    def location_is_valid(self, CBlock block, CellIdx x, CellIdx y, CellIdx z):
        cdef CellIdx loc[3]
        loc[:] = x, y, z
        return box_location_is_valid(&self.c, &block.c, loc)

    def coord(self):
        if self.equipment:
            return self.equipment.attached_coord(self.teu)
        elif BOX_STATE_STORED <= self.state < BOX_STATE_RETRIEVING:
            if self.state == BOX_STATE_RESHUFFLING:
                return self.block.cell_coord(self.previous_loc, None, self.teu)
            return self.block.box_coord(self, None)

    def __repr__(self):
        return "Box[{}'|{}]".format(self.size, self.c.id.decode("utf-8"))

