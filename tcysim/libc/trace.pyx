cimport cython

@cython.freelist(512)
cdef class Paths:
    def __init__(self, int chunk_size):
        pathtrace_init(&self.c, chunk_size)

    def __destroy__(self):
        pathtrace_destroy(&self.c)

    def append(self, Time time, float pos):
        pathtrace_append_frame(&self.c, time, pos, NULL)

    def intersect_test(self, Paths other, float clearance, float shift):
        return pathtrace_intersect_test_with_clearance(&self.c, &other.c, clearance, shift)

    @property
    def max(self):
        return self.c.max

    @property
    def min(self):
        return self.c.min
