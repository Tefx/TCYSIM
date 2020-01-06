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

    def __destroy__(self):
        box_destroy(&self.c)

    def alloc(self, time, block, loc):
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
        if self.state == BOX_STATE_STORING:
            box_store(&self.c, time)
        elif self.state == BOX_STATE_RELOCATING:
            box_relocate_store(&self.c, time)

    def retrieve(self, int time):
        if self.c._holder_or_origin:
            box_relocate_retrieve(&self.c, time)
        else:
            box_retrieve(&self.c, time)

    def start_store(self):
        self.state = BOX_STATE_STORING

    def finish_retrieve(self):
        self.state = BOX_STATE_RETRIEVED

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
        elif self.state == BOX_STATE_STORED:
            return self.block.box_coord(self, None)

    def __repr__(self):
        return "Box[{}'|{}]".format(self.size, self.c.id.decode("utf-8"))
