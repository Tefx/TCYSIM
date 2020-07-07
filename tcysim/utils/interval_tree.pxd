from libc.stdint cimport uint32_t, uint64_t


cdef extern from "interval_tree.h":
    ctypedef double IntervalNum

    ctypedef struct IntervalNode_TCY:
        IntervalNode_TCY *children[2]
        uint32_t height
        double sub_high
        IntervalNum start, end
        uint64_t ref_count

    ctypedef struct IntervalTree_TCY:
        IntervalNode_TCY *root

    ctypedef void (*IntervalNodeProcessor)(IntervalNode_TCY *, void *)

    void interval_tree_init(IntervalTree_TCY *tree);
    void interval_node_destroy(IntervalNode_TCY *node);
    IntervalNode_TCY *interval_tree_insert(IntervalTree_TCY *tree, IntervalNum start, IntervalNum end)
    IntervalNode_TCY *interval_tree_delete(IntervalTree_TCY *tree, IntervalNode_TCY *node2del)
    IntervalNode_TCY *interval_tree_update(IntervalTree_TCY *tree, IntervalNode_TCY *node,
                                           IntervalNum new_start, IntervalNum new_end)
    void interval_tree_process_overlapped(IntervalTree_TCY *tree,
                                          IntervalNum interval_start, IntervalNum interval_end,
                                          IntervalNodeProcessor processor, void *data)

cdef class Interval:
    cdef IntervalNode_TCY *c
    cdef IntervalTree tree
    cpdef void remove_from_tree(self)
    cpdef void update(self, double start, double end)

cdef class IntervalTree:
    cdef IntervalTree_TCY c
    cdef double min_len
    cpdef Interval insert(self, double start, double end)
    cpdef void delete(self, Interval node)
    cpdef void update(self, Interval node, double new_start, double new_end)
    cpdef void process_overlapped(self, double start, double end, processor)
