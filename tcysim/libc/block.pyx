from cpython cimport PyObject


cdef class CBlock:
    def __init__(self, spec, int stacking_axis=2, tuple sync_axes=(0, 2)):
        cdef CellIdx c_spec[3];
        cdef bool c_sync[3];
        c_spec[:] = spec
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
        loc[:] = [x, y, z]
        res = block_usage(&self.c, loc, include_occupied)
        return res

    def box_at(self, loc):
        cdef CellIdx pos[3]
        pos[:] = loc
        cdef Box*box = block_box_at(&self.c, pos)
        return <object> box._self

    def top_box(self, loc, along):
        cdef CellIdx pos[3]
        pos[:] = loc
        cdef Box* box = block_top_box(&self.c, pos, along)
        return <object> box._self

    def stack_hash(self, loc):
        cdef CellIdx pos[3]
        pos[:] = loc
        return blk_stack_hash(&self.c, pos)

    def lock(self, loc):
        cdef CellIdx pos[3]
        pos[:] = loc
        block_lock(&self.c, pos)

    def unlock(self, loc):
        cdef CellIdx pos[3]
        pos[:] = loc
        block_unlock(&self.c, pos)

    def is_locked(self, loc):
        cdef CellIdx pos[3]
        pos[:] = loc
        return block_is_locked(&self.c, pos)
