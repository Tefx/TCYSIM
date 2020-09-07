from .define cimport *
from .block cimport CBlock
from tcysim.utils.vector cimport V3, V3i
from cpython cimport PyObject

cdef class CBoxState:
    INITIAL = BOX_STATE_INITIAL
    ALLOCATED = BOX_STATE_ALLOCATED
    STORING = BOX_STATE_STORING
    STORED = BOX_STATE_STORED
    RELOCATING = BOX_STATE_RELOCATING
    RETRIEVING = BOX_STATE_RETRIEVING
    RETRIEVED = BOX_STATE_RETRIEVED
    PLACEHOLDER = BOX_STATE_PLACEHOLDER

cdef class CBox:
    def __init__(self, bytes box_id, int size=20, *args, **kwargs):
        cdef BoxSize_TCY c_size
        if size == 20:
            c_size = BOX_SIZE_TWENTY
        elif size == 40:
            c_size = BOX_SIZE_FORTY
        else:
            raise NotImplementedError
        box_init(&self.c, box_id, c_size)
        self.c._self = <PyObject*> self
        self.equipment = None

    def __dealloc__(self):
        box_destroy(&self.c)

    def alloc(self, Time_TCY time, CBlock block, V3 loc):
        cdef CellIdx_TCY new_loc[3];

        if block is not None:
            block.hook_before_alloc(self, loc)
        else:
            (<CBlock>self.c.block._self).hook_before_alloc(self, loc)

        if self.c.state == BOX_STATE_INITIAL:
            self.set_location(block, loc.x, loc.y, loc.z)
            box_alloc(&self.c, time)
        elif self.c.state == BOX_STATE_ALLOCATED:
            if not self.c._holder_or_origin:
                loc.cpy2mem_i(new_loc)
                box_realloc(&self.c, time, new_loc)
            else:
                raise Exception("triple alloc")
        elif self.c.state == BOX_STATE_STORED:
            if not self.c._holder_or_origin:
                loc.cpy2mem_i(new_loc)
                box_relocate_alloc(&self.c, time, new_loc)
        elif self.c.state == BOX_STATE_RETRIEVING:
            self.set_location(block, loc.x, loc.y, loc.z)
            box_alloc(&self.c, time)
            self.c.state = BOX_STATE_RETRIEVING
        else:
            raise NotImplementedError

    def realloc(self, Time_TCY time, CBlock block, V3 loc):
        cdef CellIdx_TCY new_loc[3];

        (<CBlock>self.c.block._self).hook_before_dealloc(self)
        block.hook_before_alloc(self, loc)

        if self.c.state != BOX_STATE_ALLOCATED:
            raise Exception("Cannot re-alloc a box with state {}".format(self.state))
        else:
            loc.cpy2mem_i(new_loc)
            box_cancel_and_realloc(&self.c, &block.c, new_loc)

    def store(self, Time_TCY time):
        (<CBlock>self.c.block._self).hook_before_store(self)

        if self.c.state == BOX_STATE_STORING:
            box_store(&self.c, time)
        elif self.c.state == BOX_STATE_RELOCATING:
            box_relocate_store(&self.c, time)
        elif self.c.state == BOX_STATE_RETRIEVING:
            box_store(&self.c, time)
        else:
            print(self.c.state)
            raise NotImplementedError

    def restore(self, Time_TCY time, block,
                CellIdx_TCY x, CellIdx_TCY y, CellIdx_TCY z,
                *args, BoxState_TCY level=BOX_STATE_STORED):
        if level == BOX_STATE_INITIAL:
            return

        self.set_location(block, x, y, z)
        box_alloc(&self.c, time)
        if level >= BOX_STATE_STORED:
            box_store(&self.c, time)

    def has_undone_relocation(self):
        return self.c._holder_or_origin is not NULL

    def retrieve(self, Time_TCY time):

        (<CBlock>self.c.block._self).hook_before_retrieve(self)

        if self.c._holder_or_origin:
            box_relocate_retrieve(&self.c, time)
            assert self.c.state == BOX_STATE_RELOCATING
        else:
            box_retrieve(&self.c, time)
            assert self.c.state == BOX_STATE_RETRIEVING

    def start_store(self, Time_TCY time):
        self.c.state = BOX_STATE_STORING

    def finish_retrieve(self, Time_TCY time):
        self.c.state = BOX_STATE_RETRIEVED

    @property
    def id(self):
        return self.c.id

    @property
    def location(self):
        return V3i(self.c.loc[0], self.c.loc[1], self.c.loc[2])

    @location.setter
    def location(self, V3 loc):
        loc.cpy2mem_i(self.c.loc)

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

    def set_location(self, CBlock block, CellIdx_TCY x, CellIdx_TCY y, CellIdx_TCY z):
        self.c.block = &block.c
        self.c.loc[0] = x
        self.c.loc[1] = y
        self.c.loc[2] = z

    cpdef V3i store_position(self, V3 new_loc=None):
        cdef CellIdx_TCY loc[3]
        if new_loc:
            new_loc.cpy2mem_i(loc)
            box_store_position(&self.c, loc, True)
        elif self.c.state == BOX_STATE_STORED:
            return self.location
        else:
            box_store_position(&self.c, loc, False)
        return V3i(loc[0], loc[1], loc[2])

    def relocate_position(self, V3 new_loc):
        cdef CellIdx_TCY loc[3]
        new_loc.cpy2mem_i(loc)
        box_relocate_position(&self.c, loc)
        return V3(loc[0], loc[1], loc[2])

    def box_above(self):
        cdef CBlock block = self.block
        cdef int axis = block.stacking_axis
        cdef CBox boc
        cdef V3 loc

        if axis < 0:
            return
        while True:
            loc = self.location
            box = block.top_box(loc, axis)
            if box is self:
                break
            yield box

    cpdef CBox top_box_above(self):
        cdef CBlock block = self.block
        cdef int axis = self.block.stacking_axis
        if axis >= 0:
            return block.top_box(self.location, axis)

    def position_is_valid(self, CBlock block, V3 loc):
        return block.position_is_valid_for_size(loc[0], loc[1], loc[2], self.teu)

    def store_coord(self, V3 loc=None, transform_to=None):
        cdef V3i idx = self.store_position(loc)
        return self.block.coord_from_cell_idx(idx, self.teu, transform_to)

    def access_coord(self, lane, transform_to=None):
        return self.block.access_coord(lane, self, transform_to)

    def current_coord(self, transform_to=None):
        cdef V3 v
        if self.equipment:
            # v = self.equipment.attached_box_coord(transform_to=self.block)
            v = self.equipment.coord_to_box(transform_to=self.block)
        elif self.c.state == BOX_STATE_STORED:
            v = self.block.box_coord(self)
        else:
            return None
        return self.block.transform_to(v, transform_to)

    def __repr__(self):
        return "Box[{}'|{}|{}]".format(self.size, self.c.id.decode("utf-8"), self.state)

    def __hash__(self):
        return self.c._hash

    def __le__(self, CBox other):
        return self.c._hash < other.c._hash