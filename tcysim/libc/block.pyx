from cpython cimport PyObject

from tcysim.utils.vector cimport V3i

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

    def __dealloc__(self):
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

    def iterboxes(self):
        cdef CellIdx_TCY pos[3], i, j, k
        cdef Box_TCY*box, *tmp
        cdef V3i loc
        for i in range(self.c.spec[0]):
            for j in range(self.c.spec[1]):
                for k in range(self.c.spec[2]):
                    pos[0] = i
                    pos[1] = j
                    pos[2] = k
                    box = block_box_at(&self.c, pos)
                    if box != NULL:
                        if box.size == BOX_SIZE_FORTY and pos[self.c.box_orientation] > 0:
                            pos[self.c.box_orientation] -= 1
                            tmp = block_box_at(&self.c, pos)
                            if tmp and tmp == box:
                                continue
                        yield V3i(i, j, k), box.state, <object> box._self

    def box_at(self, V3 loc):
        cdef CellIdx_TCY pos[3]
        loc.cpy2mem_i(pos)
        cdef Box_TCY*box = block_box_at(&self.c, pos)
        return <object> box._self

    cpdef object top_box(self, V3 loc, int along):
        cdef CellIdx_TCY pos[3]
        loc.cpy2mem_i(pos)
        cdef Box_TCY*box = block_top_box(&self.c, pos, along)
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

    cpdef array.array all_column_usage(self, int axis=-1, bint include_occupied=True, array.array avail=None,
                                       array.array res=None):
        cdef CellIdx_TCY size

        if axis < 0:
            axis = self.stacking_axis

        cdef array.array results
        if res is None:
            results = array.array("i")

            size = 1
            for i in range(3):
                if i != axis:
                    size *= self.c.spec[i]

            array.resize(results, size)
        else:
            results = res

        if avail is None:
            block_all_column_usages(&self.c, axis, include_occupied, NULL, results.data.as_ints)
        else:
            block_all_column_usages(&self.c, axis, include_occupied, avail.data.as_ints, results.data.as_ints)

        return results

    cpdef array.array all_slot_usage(self, int norm_axis, bint include_occupied=True, array.array avail=None,
                                     array.array res=None):

        cdef array.array results
        if res is None:
            results = array.array("i")
            array.resize(results, self.c.spec[norm_axis])
        else:
            results = res

        if avail is None:
            block_all_slot_usages(&self.c, norm_axis, include_occupied, NULL, results.data.as_ints)
        else:
            block_all_slot_usages(&self.c, norm_axis, include_occupied, avail.data.as_ints, results.data.as_ints)
        return results

    cpdef array.array all_slot_states(self, int norm_axis, array.array res=None):
        cdef array.array results
        if res is None:
            results = array.array("i")
            array.resize(results, self.c.spec[norm_axis])
        else:
            results = res
        block_all_slot_states(&self.c, norm_axis, results.data.as_ints)
        return results

    cpdef array.array validate_all_slots(self, int norm_axis, int teu, array.array res=None):
        cdef array.array results
        if res is None:
            results = array.array("i")
            array.resize(results, self.c.spec[norm_axis])
        else:
            results = res

        if teu == 1:
            block_validate_all_slots_for_size(&self.c, norm_axis, BOX_SIZE_TWENTY, results.data.as_ints)
        else:
            block_validate_all_slots_for_size(&self.c, norm_axis, BOX_SIZE_FORTY, results.data.as_ints)
        return results

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
