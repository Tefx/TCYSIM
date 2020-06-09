from cpython cimport PyObject, Py_INCREF, Py_DECREF


cdef class IdxSet:
    def __cinit__(self, size=10240):
        idxset_init(&self.c, size=size)

    def __dealloc__(self):
        idxset_destroy(&self.c)

    def add(self, item):
        idx = idxset_add(&self.c, <PyObject*>item)
        if idx < 0:
            raise MemoryError("set is full")
        Py_INCREF(item)
        return idx

    def __getitem__(self, idx_t idx):
        cdef void* ptr = idxset_get(&self.c, idx)
        if ptr == NULL:
            raise KeyError(idx)
        return <object>ptr

    def __setitem__(self, idx_t idx, new_item):
        cdef void* old_ptr = idxset_update(&self.c, idx, <PyObject*>new_item)
        if old_ptr == NULL:
            raise KeyError(idx)
        Py_INCREF(new_item)
        old_item = <object>old_ptr
        Py_DECREF(old_item)

    def __delitem__(self, idx_t idx):
        self.pop(idx)

    cpdef pop(self, idx_t idx):
        cdef void* ptr = idxset_pop(&self.c, idx)
        if ptr == NULL:
            raise KeyError(idx)
        obj = <object>ptr
        Py_DECREF(obj)
        return obj
