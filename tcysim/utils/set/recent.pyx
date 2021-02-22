from libc.stdlib cimport malloc, free
from cpython cimport PyObject, Py_INCREF, Py_XDECREF

from pesim.math_aux cimport time_le

cdef class RecentSet:
    def __init__(self, double days=0, double hours=0, double minutes=0, double seconds=0):
        self.period = seconds + (minutes + (hours + days * 24) * 60) * 60
        self.head = NULL
        self.tail = NULL

    def add(self, double time, object item):
        cdef _rs_node* node = <_rs_node*>malloc(sizeof(_rs_node))
        node.time = time
        node.pointer = <PyObject*>item
        node.next = NULL
        Py_INCREF(item)

        if self.tail == NULL:
            self.tail = self.head = node
        else:
            self.tail.next = node
            self.tail = node

        cdef _rs_node* tmp
        while self.head != NULL and time_le(self.head.time + self.period, time):
            tmp = self.head
            self.head = tmp.next

            Py_XDECREF(<PyObject*>(tmp.pointer))
            free(tmp)

        if self.head == NULL:
            self.tail = NULL

    def __iter__(self):
        cdef _rs_node* p = self.head
        while p != NULL:
            yield <object>p.pointer
            p = p.next

