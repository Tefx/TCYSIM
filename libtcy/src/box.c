//
// Created by tefx on 10/22/19.
//

#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include "../include/box.h"
#include "../include/block.h"
#include "../include/define.h"
#include "../include/error.h"

static inline void _box_mark_usage(Block_TCY *blk, Box_TCY *box, int delta) {
    for (int i = 0; i < 3; ++i) {
        if (blk->column_use_type[i]) {
            if (delta > 0 && BLK_USAGE_OCCUPIED(blk, box->loc, i) == 1) {
                if (box->size == BOX_SIZE_TWENTY) {
                    blk->column_use_type[i][_blk_clmn_idx(blk, box->loc, i)] = SLOT_USAGE_TWENTY_ONLY;
                } else if (box->size == BOX_SIZE_FORTY) {
                    blk->column_use_type[i][_blk_clmn_idx(blk, box->loc, i)] = SLOT_USAGE_FORTY_ONLY;
                    box->loc[blk->box_orientation]++;
                    BLK_USE_TYPE(blk, box->loc, i) = SLOT_USAGE_FORTY_ONLY_END;
                    box->loc[blk->box_orientation]--;
                }
            } else if (delta < 0 && BLK_USAGE_OCCUPIED(blk, box->loc, i) == 0) {
                blk->column_use_type[i][_blk_clmn_idx(blk, box->loc, i)] = SLOT_USAGE_FREE;
                if (box->size == BOX_SIZE_FORTY) {
                    box->loc[blk->box_orientation]++;
                    blk->column_use_type[i][_blk_clmn_idx(blk, box->loc, i)] = SLOT_USAGE_FREE;
                    box->loc[blk->box_orientation]--;
                }
            }
        }
    }
}

static inline void _box_adjust_usage(Block_TCY *blk, Box_TCY *box, int delta, bool occupied) {
    if (occupied) {
        for (int i = 0; i < 3; ++i) {
            BLK_USAGE_OCCUPIED(blk, box->loc, i) += delta;

            if (BLK_USAGE_OCCUPIED(blk, box->loc, i) < 0 || BLK_USAGE_OCCUPIED(blk, box->loc, i) > blk->spec[i])
                printf("warning[OC]: %s i=%d s=%d d=%d (%d, %d, %d) %d\n", box->id, i, box->state, delta, box->loc[0],
                       box->loc[1], box->loc[2], BLK_USAGE_OCCUPIED(blk, box->loc, i));
            assert(BLK_USAGE_OCCUPIED(blk, box->loc, i) >= 0 && BLK_USAGE_OCCUPIED(blk, box->loc, i) <= blk->spec[i]);
        }
    } else {
        for (int i = 0; i < 3; ++i) {
            BLK_USAGE(blk, box->loc, i) += delta;

            if (BLK_USAGE(blk, box->loc, i) < 0 || BLK_USAGE(blk, box->loc, i) > blk->spec[i])
                printf("warning[OC]: %s i=%d s=%d d=%d (%d, %d, %d) %d\n", box->id, i, box->state, delta, box->loc[0],
                       box->loc[1], box->loc[2], BLK_USAGE(blk, box->loc, i));
            assert(BLK_USAGE(blk, box->loc, i) >= 0 && BLK_USAGE(blk, box->loc, i) <= blk->spec[i]);
        }
    }
}

static inline void _box_adjust_and_mark_usage(Block_TCY *blk, Box_TCY *box, int delta, bool occupied) {
    _box_adjust_usage(blk, box, delta, occupied);
    if (box->size == BOX_SIZE_FORTY) {
        box->loc[blk->box_orientation]++;
        _box_adjust_usage(blk, box, delta, occupied);
        box->loc[blk->box_orientation]--;
    }
    if (occupied)
        _box_mark_usage(blk, box, delta);
}

int _box_swap(Box_TCY *box, int along) {
    Block_TCY *blk = box->block;
    Box_TCY *box2 = _blk_neighbor_box(blk, box, along, TRUE);

    _blk_unlink_cell(blk, box);
    _box_adjust_and_mark_usage(blk, box, -1, TRUE);
    if (box->state == BOX_STATE_STORED)
        _box_adjust_and_mark_usage(blk, box, -1, FALSE);

    _blk_unlink_cell(blk, box);
    _box_adjust_and_mark_usage(blk, box2, -1, TRUE);
    if (box2->state == BOX_STATE_STORED)
        _box_adjust_and_mark_usage(blk, box2, -1, FALSE);

    int32_t tmp = box->loc[along];
    box->loc[along] = box2->loc[along];
    if (box->size == box2->size) {
        box2->loc[along] = tmp;
    } else if (box->size == BOX_SIZE_FORTY && box2->size == BOX_SIZE_TWENTY) {
        box2->loc[along] = tmp + 1;
    } else if (box->size == BOX_SIZE_TWENTY && box2->size == BOX_SIZE_FORTY) {
        box2->loc[along] = tmp - 1;
    } else {
        return ERROR_UNKNOWN_BOX_SIZE;
    }

    _blk_link_cell(blk, box);
    _box_adjust_and_mark_usage(blk, box, 1, TRUE);
    if (box->state == BOX_STATE_STORED)
        _box_adjust_and_mark_usage(blk, box, 1, FALSE);

    _blk_link_cell(blk, box2);
    _box_adjust_and_mark_usage(blk, box2, 1, TRUE);
    if (box2->state == BOX_STATE_STORED)
        _box_adjust_and_mark_usage(blk, box2, 1, FALSE);

    return SUCCEED;
}

static inline int _box_sink(Box_TCY *box) {
    Block_TCY *blk = box->block;
    if (blk->stacking_axis < 0) return ERROR_CANNOT_FIND_STACKING_AXIS;
    int32_t along = blk->stacking_axis;
    Box_TCY *box2;
    while (box->loc[along] > 0) {
        box2 = _blk_neighbor_box(blk, box, along, FALSE);
        if (box2->state != BOX_STATE_STORED)
            _box_swap(box2, along);
        else
            break;
    }
    return SUCCEED;
}

static inline int _box_float(Box_TCY *box) {
    Block_TCY *blk = box->block;
    if (blk->stacking_axis < 0) return ERROR_CANNOT_FIND_STACKING_AXIS;
    int32_t along = blk->stacking_axis;
    Box_TCY *box2;
    while (box->loc[along] < blk->spec[along]) {
        box2 = _blk_neighbor_box(blk, box, along, TRUE);
//        if (box2 && box2->state != BOX_STATE_STORED)
        if (box2) {
            if (box2->state == BOX_STATE_STORED)
                printf("Warning: floating under stored, this should only happen when restoring from snapshots!");
            _box_swap(box, along);
        } else
            break;
    }
    return SUCCEED;
}

void box_init(Box_TCY *box, char *box_id, BoxSize_TCY size) {
    strcpy(box->id, box_id);
    box->size = size;
    box->state = BOX_STATE_INITIAL;
    box->alloc_time = box->store_time = box->retrieval_time = TIME_INF;
    box->_holder_or_origin = NULL;
}

void box_destroy(Box_TCY *box) {}

int box_alloc(Box_TCY *box, Time_TCY time) {
    struct Block_TCY *blk = box->block;
    CellIdx_TCY *loc = box->loc;

    if (time >= 0)
        box->alloc_time = time;

    if (blk->stacking_axis >= 0) {
        loc[blk->stacking_axis] = BLK_USAGE_OCCUPIED(blk, loc, blk->stacking_axis);
    }

    assert(!(loc[0] < 0 || loc[1] < 0 || loc[2] < 0));
//        return ERROR_ALLOC_CELL_MISSING_LOCATION_INFO;

    assert(block_position_is_valid_for_size(blk, loc, box->size));
//        return ERROR_INVALID_LOCATION;

    _blk_link_cell(blk, box);
    _box_adjust_and_mark_usage(blk, box, 1, TRUE);

    if (time >= 0 && box->state != BOX_STATE_PLACEHOLDER)
        box->state = BOX_STATE_ALLOCATED;

    return SUCCEED;
}


void box_store_position(Box_TCY *box, CellIdx_TCY *idx, bool new_loc) {
    Block_TCY *blk = box->block;
    if (!new_loc)
        memcpy(idx, box->loc, sizeof(CellIdx_TCY) * 3);
    _blk_top_of_stack(blk, idx);
}

int box_store(Box_TCY *box, Time_TCY time) {
    Block_TCY *blk = box->block;

    if (time >= 0 && box->state != BOX_STATE_RELOCATING)
        box->store_time = time;

    if (blk->stacking_axis >= 0)
        _box_sink(box);

    _box_adjust_and_mark_usage(blk, box, 1, FALSE);
    box->state = BOX_STATE_STORED;

    return SUCCEED;
}

int box_retrieve(Box_TCY *box, Time_TCY time) {
    Block_TCY *blk = box->block;

    if (time >= 0)
        box->retrieval_time = time;

    if (blk->stacking_axis >= 0)
        _box_float(box);

    _blk_unlink_cell(blk, box);
    _box_adjust_and_mark_usage(blk, box, -1, TRUE);
    if (box->state == BOX_STATE_STORED)
        _box_adjust_and_mark_usage(blk, box, -1, FALSE);

    if (time >= 0)
        box->state = BOX_STATE_RETRIEVING;
    return SUCCEED;
}

int box_place_holder(Box_TCY *box, CellIdx_TCY *new_loc) {
    Box_TCY *holder = (Box_TCY *) malloc(sizeof(Box_TCY));
    memcpy(holder, box, sizeof(Box_TCY));
    holder->state = BOX_STATE_PLACEHOLDER;
    holder->_holder_or_origin = box;

    int res;
    if (new_loc) {
        memcpy(holder->loc, new_loc, sizeof(CellIdx_TCY) * 3);
        if ((res = box_alloc(holder, -1)) != SUCCEED)
            return res;
    } else {
        _blk_unlink_cell(box->block, box);
        _blk_link_cell(holder->block, holder);
    }

    box->_holder_or_origin = holder;
    return SUCCEED;
}

int box_remove_holder(Box_TCY *box) {
    Box_TCY *holder = box->_holder_or_origin;
    int res;

    if ((res = box_retrieve(holder, -1)) != SUCCEED)
        return res;

    box_destroy(box->_holder_or_origin);
    free(box->_holder_or_origin);

    box->_holder_or_origin = NULL;
    return SUCCEED;
}

int box_cancel_alloc(Box_TCY* box){
    if (box->state != BOX_STATE_ALLOCATED)
        return ERROR_BOX_ALREADY_STORED;
    struct Block_TCY *blk = box->block;
    _box_adjust_and_mark_usage(blk, box, -1, TRUE);
    _blk_unlink_cell(blk, box);
    return SUCCEED;
}

int box_cancel_and_realloc(Box_TCY* box, Block_TCY *blk, CellIdx_TCY* new_loc){
    int res;
    if ((res=box_cancel_alloc(box)) != SUCCEED)
        return res;
    box->block = blk;
    memcpy(box->loc, new_loc, sizeof(CellIdx_TCY) * 3);
    return box_alloc(box, -1);
}

int box_realloc(Box_TCY *box, Time_TCY time, CellIdx_TCY *new_loc) {
    box_place_holder(box, NULL);

    memcpy(box->loc, new_loc, sizeof(CellIdx_TCY) * 3);
    int res = box_alloc(box, -1);
    return res;
}

void box_relocate_position(Box_TCY *box, CellIdx_TCY *loc) {
    box_store_position(box->_holder_or_origin, loc, 0);
}

int box_relocate_alloc(Box_TCY *box, Time_TCY time, CellIdx_TCY *new_loc) {
    return box_place_holder(box, new_loc);
}

int box_relocate_retrieve(Box_TCY *box, Time_TCY time) {
    int res;
    if ((res = box_retrieve(box, -1)) != SUCCEED) {
        assert(res == SUCCEED);
        return res;
    }
//    printf("%s relocating\n", box->id);
    box->state = BOX_STATE_RELOCATING;
    return SUCCEED;
}

int box_relocate_store(Box_TCY *box, Time_TCY time) {
    assert(box->_holder_or_origin);
    memcpy(box->loc, box->_holder_or_origin->loc, sizeof(CellIdx_TCY) * 3);
    box_remove_holder(box);
    box_alloc(box, -1);
    return box_store(box, -1);
}

