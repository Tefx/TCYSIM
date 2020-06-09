ctypedef struct _rs_node:
    double time
    void* pointer
    _rs_node* next


cdef class RecentSet:
    cdef double period
    cdef _rs_node* head
    cdef _rs_node* tail

