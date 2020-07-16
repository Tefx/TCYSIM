from cpython cimport PyObject, Py_INCREF, Py_DECREF


cdef class Interval:
    def __init__(self, IntervalTree tree, double start, double end):
        self.c = interval_tree_insert(&tree.c, start, end)
        self.tree = tree

    def __del__(self):
        if self.c is not NULL:
            self.tree.delete(self)

    cpdef void remove_from_tree(self):
        if self.c is not NULL:
            self.tree.delete(self)

    @property
    def start(self):
        return self.c.start

    @start.setter
    def start(self, double value):
        self.tree.update(self, value, self.c.end)

    @property
    def end(self):
        return self.c.end

    @end.setter
    def end(self, double value):
        self.tree.update(self, self.c.start, value)

    @property
    def interval(self):
        return self.c.start, self.c.end

    @interval.setter
    def interval(self, tuple value):
        cdef double start, end
        start, end = value
        self.tree.update(self, start, end)

    cpdef void update(self, double start, double end):
        self.tree.update(self, start, end)

cdef void _processor(IntervalNode_TCY *node, void*processor):
    (<object> processor)(node.start, node.end, node.ref_count)

cdef class IntervalTree:
    def __cinit__(self, double min_len=0):
        interval_tree_init(&self.c)
        self.min_len = min_len

    cpdef Interval insert(self, double start, double end):
        return Interval(self, start, end)

    cpdef void delete(self, Interval node):
        interval_tree_delete(&self.c, node.c)
        node.c = NULL

    cpdef void update(self, Interval node, double new_start, double new_end):
        if new_end < new_start + self.min_len:
            new_end = new_start + self.min_len
        node.c = interval_tree_update(&self.c, node.c, new_start, new_end)

    cpdef void process_overlapped(self, double start, double end, processor):
        interval_tree_process_overlapped(&self.c, start, end, _processor, <PyObject*> processor)
