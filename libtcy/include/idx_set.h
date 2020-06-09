//
// Created by tefx on 2/5/20.
//

#ifndef LIBTCY_IDX_SET_H
#define LIBTCY_IDX_SET_H

#include "../include/define.h"

#include <stdint.h>

typedef int64_t idx_t;

typedef struct IdxNode_ {
    idx_t idx;
    void* pointer;
    struct IdxNode_ *next;
} IdxNode_C;

typedef struct {
    idx_t size;
    IdxNode_C* nodes;
    IdxNode_C* avail_head;
} IdxSet_C;

DLLEXPORT void idxset_init(IdxSet_C* ixst, idx_t size);
DLLEXPORT void idxset_destroy(IdxSet_C* ixst);
DLLEXPORT idx_t idxset_add(IdxSet_C* ixst, void* item);
DLLEXPORT void* idxset_get(IdxSet_C* ixst, idx_t idx);
DLLEXPORT void* idxset_pop(IdxSet_C* ixst, idx_t idx);
void* idxset_update(IdxSet_C *ixst, idx_t idx, void* item);

#endif //LIBTCY_IDX_SET_H
