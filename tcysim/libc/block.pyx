from cpython cimport PyObject

cdef class BlockColumnUsage:
    FREE = SLOT_USAGE_FREE
    TWENTY_ONLY = SLOT_USAGE_TWENTY_ONLY
    FORTY_ONLY = SLOT_USAGE_FORTY_ONLY
    FORTY_ONLY_END = SLOT_USAGE_FORTY_ONLY_END

cdef class CBlock:
    def __init__(self, V3 spec, int stacking_axis=2, tuple sync_axes=(0, 2)):
        cdef CellIdx_TCY c_spec[3];
        cdef bool c_sync[3];
        spec.cpy2mem_i(c_spec)
        c_sync[:] = [1 if i in sync_axes else 0 for i in range(3)]
        block_init(&self.c, c_spec, 0, stacking_axis, c_sync)
        self.c._self = <PyObject*> self

    def __destroy__(self):
        block_destroy(&self.c)

    @property
    def COLUMN_USAGE(self):
        return BlockColumnUsage

    @property
    def stacking_axis(self):
        return self.c.stacking_axis

    cpdef int count(self, int x=-1, int y=-1, int z=-1, bint include_occupied=True):
        cdef CellIdx_TCY loc[3]
        loc[0] = x
        loc[1] = y
        loc[2] = z
        res = block_usage(&self.c, loc, include_occupied)
        return res

    def box_at(self, V3 loc):
        cdef CellIdx_TCY pos[3]
        loc.cpy2mem_i(pos)
        cdef Box_TCY*box = block_box_at(&self.c, pos)
        return <object> box._self

    cpdef object top_box(self, V3 loc, int along):
        cdef CellIdx_TCY pos[3]
        loc.cpy2mem_i(pos)
        cdef Box_TCY* box = block_top_box(&self.c, pos, along)
        return <object> box._self

    def stack_hash(self, V3 loc):
        cdef CellIdx_TCY pos[3]
        loc.cpy2mem_i(pos)
        return blk_stack_hash(&self.c, pos)

    cpdef SlotUsage_TCY column_state(self, int x, int y, int z, int axis):
        cdef CellIdx_TCY pos[3]
        pos[0] = x
        pos[1] = y
        pos[2] = z
        return block_column_state(&self.c, pos, axis)

    cpdef bint position_is_valid_for_size(self, int x, int y, int z, int teu):
        cdef CellIdx_TCY pos[3]
        cdef bint res
        pos[0] = x
        pos[1] = y
        pos[2] = z
        # loc.cpy2mem_i(pos)

        if teu == 1:
            res = block_position_is_valid_for_size(&self.c, pos, BOX_SIZE_TWENTY)
        else:
            res = block_position_is_valid_for_size(&self.c, pos, BOX_SIZE_FORTY)
        return res

    def lock(self, V3 loc):
        cdef CellIdx_TCY pos[3]
        loc.cpy2mem_i(pos)
        block_lock(&self.c, pos)

    def unlock(self, V3 loc):
        cdef CellIdx_TCY pos[3]
        loc.cpy2mem_i(pos)
        block_unlock(&self.c, pos)

    def is_locked(self, V3 loc):
        cdef CellIdx_TCY pos[3]
        loc.cpy2mem_i(pos)
        return block_is_locked(&self.c, pos)
