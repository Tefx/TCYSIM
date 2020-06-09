from libc.stdint cimport int64_t

cdef extern from "idx_set.h":
    ctypedef int64_t idx_t
    ctypedef struct IdxNode_C

    ctypedef struct IdxSet_C:
        idx_t size
        IdxNode_C* nodes
        IdxNode_C* avail_head

    void idxset_init(IdxSet_C* ixst, idx_t size)
    void idxset_destroy(IdxSet_C* ixst)
    idx_t idxset_add(IdxSet_C* ixst, void* item)
    void* idxset_get(IdxSet_C* ixst, idx_t idx)
    void* idxset_pop(IdxSet_C* ixst, idx_t idx)
    void* idxset_update(IdxSet_C *ixst, idx_t idx, void* item)


cdef class IdxSet:
    cdef IdxSet_C c

    cpdef pop(self, idx_t idx)
