//
// Created by tefx on 5/21/20.
//

#include "../include/interval_tree.h"

#include <stdlib.h>
#include <stdio.h>
#include <assert.h>

#define _LEFT_CHILD 0
#define _RIGHT_CHILD 1

#define _NODE_DEC_REF(node) ((node)->ref_count--)
#define _NODE_INC_REF(node) ((node)->ref_count++)
#define _NODE_HEIGHT(node) ((node)?(node)->height:0)
#define _NODE_SUB_HIGH(node) ((node)?(node)->sub_high:0)

#define _EPSILON 1e-2
#define _NUM_EQ(a, b) (((a) <= (b) + _EPSILON) && ((b) - _EPSILON <= (a)))
#define _NUM_LT(a, b) ((a) < (b) - _EPSILON)

inline int interval_eq(IntervalNode_TCY *a, IntervalNum start, IntervalNum end) {
    return _NUM_EQ(a->start, start) && _NUM_EQ(a->end, end);
}

inline int interval_lt(IntervalNode_TCY *a, IntervalNum start, IntervalNum end) {
    return _NUM_LT(a->start, start) || (_NUM_EQ(a->start, start) && _NUM_LT(a->end, end));
}

inline int interval_overlap(IntervalNode_TCY *a, IntervalNum start, IntervalNum end) {
    return _NUM_LT(start, a->end) && _NUM_LT(a->start, end);
}

IntervalNode_TCY *interval_node_new(const double start, const double end) {
    IntervalNode_TCY *node = (IntervalNode_TCY *) malloc(sizeof(IntervalNode_TCY));
    node->start = start;
    node->sub_high = node->end = end;

    node->height = 1;
    node->ref_count = 0;
    node->children[0] = node->children[1] = NULL;

    return node;
}

inline void interval_node_reuse(IntervalNode_TCY *node, const double start, const double end) {
    assert(node->ref_count == 1);

    node->start = start;
    node->sub_high = node->end = end;
    node->height = 1;
    node->children[0] = node->children[1] = NULL;
}

void interval_node_destroy(IntervalNode_TCY *node) {
    if (node) {
        _NODE_DEC_REF(node);
        if (!node->ref_count)
            free(node);
    }
}

inline void interval_node_fix_height(IntervalNode_TCY *node) {
    node->height = MAX(_NODE_HEIGHT(node->children[_LEFT_CHILD]),
                       _NODE_HEIGHT(node->children[_RIGHT_CHILD])) + 1;
}

inline void interval_node_fix_subhigh(IntervalNode_TCY *node) {
    node->sub_high = MAX(node->end, _NODE_SUB_HIGH(node->children[_LEFT_CHILD]));
    node->sub_high = MAX(node->sub_high, _NODE_SUB_HIGH(node->children[_RIGHT_CHILD]));
}

inline void interval_node_fix_height_and_subhigh(IntervalNode_TCY *node) {
    node->height = MAX(_NODE_HEIGHT(node->children[_LEFT_CHILD]),
                       _NODE_HEIGHT(node->children[_RIGHT_CHILD])) + 1;
    node->sub_high = MAX(node->end, _NODE_SUB_HIGH(node->children[_LEFT_CHILD]));
    node->sub_high = MAX(node->sub_high, _NODE_SUB_HIGH(node->children[_RIGHT_CHILD]));
}

inline IntervalNode_TCY *interval_node_rotate(IntervalNode_TCY *node, int child_idx) {
    IntervalNode_TCY *new_root = node->children[child_idx];
    node->children[child_idx] = new_root->children[!child_idx];
    new_root->children[!child_idx] = node;

    interval_node_fix_height_and_subhigh(node);
    interval_node_fix_height_and_subhigh(new_root);

    return new_root;

}

IntervalNode_TCY *interval_node_rebalance_and_fix(IntervalNode_TCY *node) {
    if (!node) return node;

    for (int d = 0; d < 2; ++d) {
        if (_NODE_HEIGHT(node->children[d]) > _NODE_HEIGHT(node->children[!d]) + 1) {
            if (_NODE_HEIGHT(node->children[d]->children[d]) <=
                _NODE_HEIGHT(node->children[d]->children[!d]))
                node->children[d] = interval_node_rotate(node->children[d], !d);
            return interval_node_rotate(node, d);
        }
    }

    interval_node_fix_height_and_subhigh(node);
    return node;
}

IntervalNode_TCY *
interval_node_insert_interval(IntervalNode_TCY *node, IntervalNum start, IntervalNum end, IntervalNode_TCY **new_node) {
    if (!node) {
        node = *new_node = interval_node_new(start, end);
    } else if (interval_eq(node, start, end)) {
        *new_node = node;
    } else {
        int idx = interval_lt(node, start, end);
        node->children[idx] = interval_node_insert_interval(node->children[idx], start, end, new_node);
        node = interval_node_rebalance_and_fix(node);
    }
    return node;
}

IntervalNode_TCY *interval_node_insert(IntervalNode_TCY *node, IntervalNode_TCY *new_node) {
    if (!node) return new_node;
    int idx = interval_lt(node, new_node->start, new_node->end);
    node->children[idx] = interval_node_insert(node->children[idx], new_node);
    return interval_node_rebalance_and_fix(node);
}

IntervalNode_TCY *interval_node_pop_min(IntervalNode_TCY *node, IntervalNode_TCY **popped) {
    if (!node->children[_LEFT_CHILD]) {
        *popped = node;
        node = node->children[_RIGHT_CHILD];
    } else {
        node->children[_LEFT_CHILD] = interval_node_pop_min(node->children[_LEFT_CHILD], popped);
        node = interval_node_rebalance_and_fix(node);
    }
    return node; //popped's sub_high & height are wrong
}

int node_in_tree(IntervalNode_TCY *root, IntervalNode_TCY *node) {
    if (!root)
        return 0;
    else if (root == node)
        return 1;
    else
        return node_in_tree(root->children[0], node) || node_in_tree(root->children[1], node);
}

int check_tree(IntervalNode_TCY *root) {
    if (root) {
        if (root->children[0]) {
            if (interval_lt(root->children[0], root->start, root->end)) {
                if (!check_tree(root->children[0]))
                    return 0;
            } else {
                printf("error left child %f %f < %f %f\n",
                       root->children[0]->start, root->children[0]->end,
                       root->start, root->end);
                printf("%d\n", interval_eq(root->children[0], root->start, root->end));
                return 0;
            }
        }
        if (root->children[1]) {
            if (interval_lt(root, root->children[1]->start, root->children[1]->end)) {
                if (!check_tree(root->children[0]))
                    return 0;
            } else {
                printf("error right child %f %f > %f %f\n",
                       root->children[1]->start, root->children[1]->end,
                       root->start, root->end);
                printf("%d\n", interval_eq(root->children[1], root->start, root->end));
                return 0;
            }
        }
    }
    return 1;
}

IntervalNode_TCY *interval_node_delete(IntervalNode_TCY *node, IntervalNode_TCY *node2del) {
    if (!node) {
        printf("Delete Error! node not in tree\n");
        assert(0);
    }

    if (node == node2del) {
        if (node->children[_RIGHT_CHILD]) {
            if (node->children[_LEFT_CHILD]) {
                IntervalNode_TCY *new_root, *new_child_root;
                new_child_root = interval_node_pop_min(node->children[_RIGHT_CHILD], &new_root);
                new_root->children[_LEFT_CHILD] = node->children[_LEFT_CHILD];
                new_root->children[_RIGHT_CHILD] = new_child_root;
                node = interval_node_rebalance_and_fix(new_root);
            } else {
                node = node->children[_RIGHT_CHILD];
            }
        } else {
            node = node->children[_LEFT_CHILD];
        }
    } else {
        int idx = interval_lt(node, node2del->start, node2del->end);
        node->children[idx] = interval_node_delete(node->children[idx], node2del);
        node = interval_node_rebalance_and_fix(node);
    }
    return node;
}

void interval_node_search(IntervalNode_TCY *node, IntervalNum start, IntervalNum end,
                          IntervalNodeProcessor processor, void *data) {
    if (_NUM_LT(start, node->sub_high)) {
        if (node->children[_LEFT_CHILD])
            interval_node_search(node->children[_LEFT_CHILD], start, end, processor, data);

        if (interval_overlap(node, start, end))
            for (uint64_t i = 0; i < node->ref_count ; ++i)
                processor(node, data);

        if (_NUM_LT(node->start, end) && node->children[_RIGHT_CHILD])
            interval_node_search(node->children[_RIGHT_CHILD], start, end, processor, data);
    }

}

void interval_tree_init(IntervalTree_TCY *tree) {
    tree->root = NULL;
}

IntervalNode_TCY *interval_tree_insert(IntervalTree_TCY *tree, IntervalNum start, IntervalNum end) {
    IntervalNode_TCY *new_node;
    tree->root = interval_node_insert_interval(tree->root, start, end, &new_node);
    _NODE_INC_REF(new_node);
    return new_node;
}

IntervalNode_TCY *interval_tree_delete(IntervalTree_TCY *tree, IntervalNode_TCY *node2del) {
    _NODE_DEC_REF(node2del);
    if (!node2del->ref_count) {
        tree->root = interval_node_delete(tree->root, node2del);
        free(node2del);
    }
    return NULL;
}

IntervalNode_TCY *interval_tree_update(IntervalTree_TCY *tree, IntervalNode_TCY *node,
                                       IntervalNum new_start, IntervalNum new_end) {
    interval_tree_delete(tree, node);
    return interval_tree_insert(tree, new_start, new_end);
}

void interval_tree_process_overlapped(IntervalTree_TCY *tree, IntervalNum interval_start, IntervalNum interval_end,
                                      IntervalNodeProcessor processor, void *data) {
    if (tree->root)
        interval_node_search(tree->root, interval_start, interval_end, processor, data);
}
