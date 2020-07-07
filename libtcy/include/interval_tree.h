//
// Created by tefx on 5/21/20.
//

#ifndef TCYLIB_INTERVAL_TREE_H
#define TCYLIB_INTERVAL_TREE_H

#include "define.h"

typedef double IntervalNum;

typedef struct it_node {
    struct it_node *children[2];
    uint32_t height;
    double sub_high;

    IntervalNum start, end;
    uint64_t ref_count;
} IntervalNode_TCY;

typedef struct {
    IntervalNode_TCY *root;
} IntervalTree_TCY;

typedef void (*IntervalNodeProcessor)(IntervalNode_TCY *, void *);

DLLEXPORT void interval_tree_init(IntervalTree_TCY *tree);

DLLEXPORT void interval_node_destroy(IntervalNode_TCY *node);

DLLEXPORT IntervalNode_TCY *interval_tree_insert(IntervalTree_TCY *tree, IntervalNum start, IntervalNum end);

DLLEXPORT IntervalNode_TCY *interval_tree_delete(IntervalTree_TCY *tree, IntervalNode_TCY *node2del);

DLLEXPORT IntervalNode_TCY *interval_tree_update(IntervalTree_TCY *tree, IntervalNode_TCY *node,
                                       IntervalNum new_start, IntervalNum new_end);

DLLEXPORT void interval_tree_process_overlapped(IntervalTree_TCY *tree,
                                      IntervalNum interval_start, IntervalNum interval_end,
                                      IntervalNodeProcessor processor, void *data);

#endif //TCYLIB_INTERVAL_TREE_H
