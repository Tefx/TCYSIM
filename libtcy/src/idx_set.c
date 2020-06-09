//
// Created by tefx on 2/5/20.
//

#include "../include/idx_set.h"
#include <malloc.h>

void idxset_init(IdxSet_C *ixst, idx_t size) {
    ixst->size = size;
    ixst->nodes = (IdxNode_C *) malloc(sizeof(IdxNode_C) * size);

    IdxNode_C *node;
    for (int i = 0; i < size; ++i) {
        node = ixst->nodes + i;
        node->pointer = NULL;
        node->idx = i;
        node->next = node + 1;
    }
    ixst->avail_head = ixst->nodes;
    ixst->nodes[size - 1].next = NULL;
}

void idxset_destroy(IdxSet_C *ixst) {
    free(ixst->nodes);
    ixst->avail_head = NULL;
}

idx_t idxset_add(IdxSet_C *ixst, void *item) {
    if (ixst->avail_head == NULL)
        return -1;

    IdxNode_C *node = ixst->avail_head;
    ixst->avail_head = node->next;
    node->pointer = item;
    return node->idx;
}

void *idxset_get(IdxSet_C *ixst, idx_t idx) {
    if (idx < 0 || idx >= ixst->size)
        return NULL;
    else
        return (ixst->nodes + idx)->pointer;
}

void* idxset_update(IdxSet_C *ixst, idx_t idx, void* item){
    void* old_item;
    IdxNode_C* node;
    if (idx < 0 || idx >= ixst->size)
        return NULL;
    else {
        node = ixst->nodes + idx;
        old_item = node->pointer;
        node->pointer = item;
        return old_item;
    }
}

void *idxset_pop(IdxSet_C *ixst, idx_t idx) {
    IdxNode_C *node = ixst->nodes + idx;
    void *item = node->pointer;
    node->pointer = NULL;
    node->next = ixst->avail_head;
    ixst->avail_head = node;
    return item;
}
