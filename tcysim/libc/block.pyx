from cpython cimport PyObject


cdef class CBlock:
    def __init__(self, V3 spec, int stacking_axis=2, tuple sync_axes=(0, 2)):
        cdef CellIdx c_spec[3];
        cdef bool c_sync[3];
        spec.cpy2mem_i(c_spec)
        c_sync[:] = [1 if i in sync_axes else 0 for i in range(3)]
        block_init(&self.c, c_spec, 0, stacking_axis, c_sync)
        self.c._self = <PyObject*> self

    def __destroy__(self):
        block_destroy(&self.c)

    @property
    def stacking_axis(self):
        return self.c.stacking_axis

    cpdef int count(self, int x=-1, int y=-1, int z=-1, bint include_occupied=True):
        cdef CellIdx loc[3]
        loc[0] = x
        loc[1] = y
        loc[2] = z
        res = block_usage(&self.c, loc, include_occupied)
        return res

    def box_at(self, V3 loc):
        cdef CellIdx pos[3]
        loc.cpy2mem_i(pos)
        cdef Box*box = block_box_at(&self.c, pos)
        return <object> box._self

    def top_box(self, V3 loc, int along):
        cdef CellIdx pos[3]
        loc.cpy2mem_i(pos)
        cdef Box* box = block_top_box(&self.c, pos, along)
        return <object> box._self

    def stack_hash(self, V3 loc):
        cdef CellIdx pos[3]
        loc.cpy2mem_i(pos)
        return blk_stack_hash(&self.c, pos)

    def column_state(self, V3 loc, int axis):
        cdef CellIdx pos[3]
        loc.cpy2mem_i(pos)
        return block_column_state(&self.c, pos, axis)

    cpdef position_is_valid_for_size(self, V3 loc, teu):
        cdef CellIdx pos[3]
        loc.cpy2mem_i(pos)
        if teu == 1:
            res = block_position_is_valid_for_size(&self.c, pos, BOX_SIZE_TWENTY)
        else:
            res = block_position_is_valid_for_size(&self.c, pos, BOX_SIZE_FORTY)
        return res

    def lock(self, V3 loc):
        cdef CellIdx pos[3]
        loc.cpy2mem_i(pos)
        block_lock(&self.c, pos)

    def unlock(self, V3 loc):
        cdef CellIdx pos[3]
        loc.cpy2mem_i(pos)
        block_unlock(&self.c, pos)

    def is_locked(self, V3 loc):
        cdef CellIdx pos[3]
        loc.cpy2mem_i(pos)
        return block_is_locked(&self.c, pos)
