//
// Created by tefx on 10/22/19.
//

#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include "box.h"
#include "block.h"
#include "define.h"
#include "error.h"

static inline bool _box_match_usage(Box *box, SlotUsage usage, SlotUsage usage2) {
    if (usage == SLOT_USAGE_FREE)
        if (box->size == BOX_SIZE_FORTY)
            return usage2 == SLOT_USAGE_FREE;
        else
            return TRUE;
    else if (usage == SLOT_USAGE_TWENTY_ONLY)
        return box->size == BOX_SIZE_TWENTY;
    else if (usage == SLOT_USAGE_FORTY_ONLY)
        return box->size == BOX_SIZE_FORTY;
    else
        return FALSE;
}

static inline void _box_mark_usage(Block *blk, Box *box, int delta) {
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

static inline void _box_adjust_usage(Block *blk, Box *box, int delta, bool occupied) {
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

static inline void _box_adjust_and_mark_usage(Block *blk, Box *box, int delta, bool occupied) {
    _box_adjust_usage(blk, box, delta, occupied);
    if (box->size == BOX_SIZE_FORTY) {
        box->loc[blk->box_orientation]++;
        _box_adjust_usage(blk, box, delta, occupied);
        box->loc[blk->box_orientation]--;
    }
    if (occupied)
        _box_mark_usage(blk, box, delta);
}

int _box_swap(Box *box, int along, bool sink) {
    Block *blk = box->block;
    Box *box2 = _blk_neighbor_box(blk, box, along, TRUE);

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

static inline int _box_sink(Box *box) {
    Block *blk = box->block;
    if (blk->stacking_axis < 0) return ERROR_CANNOT_FIND_STACKING_AXIS;
    int32_t along = blk->stacking_axis;
    Box *box2;
    while (box->loc[along] > 0) {
        box2 = _blk_neighbor_box(blk, box, along, FALSE);
        if (box2->state != BOX_STATE_STORED)
            _box_swap(box2, along, TRUE);
        else
            break;
    }
    return SUCCEED;
}

static inline int _box_float(Box *box) {
    Block *blk = box->block;
    if (blk->stacking_axis < 0) return ERROR_CANNOT_FIND_STACKING_AXIS;
    int32_t along = blk->stacking_axis;
    Box *box2;
    while (box->loc[along] < blk->spec[along]) {
        box2 = _blk_neighbor_box(blk, box, along, TRUE);
        if (box2 && box2->state != BOX_STATE_STORED)
            _box_swap(box, along, FALSE);
        else
            break;
    }
    return SUCCEED;
}

void box_init(Box *box, char *box_id, BoxSize size) {
    strcpy(box->id, box_id);
    box->size = size;
    box->state = BOX_STATE_INITIAL;
    box->alloc_time = box->store_time = box->retrieval_time = TIME_INF;
    box->_holder_or_origin = NULL;
}

void box_destroy(Box *box) {}

bool box_position_is_valid(Box *box, Block *blk, CellIdx *loc) {
    SlotUsage column_use_type, column_use_type2 = SLOT_USAGE_FREE;
    if (box->size == BOX_SIZE_FORTY && loc[blk->box_orientation] > blk->spec[blk->box_orientation] - 2)
        return FALSE;
    for (int i = 0; i < 3; ++i) {
        if (blk->column_use_type[i]) {
            column_use_type = blk->column_use_type[i][_blk_clmn_idx(blk, loc, i)];
            if (box->size == BOX_SIZE_FORTY) {
                loc[blk->box_orientation]++;
                column_use_type2 = blk->column_use_type[i][_blk_clmn_idx(blk, loc, i)];
                loc[blk->box_orientation]--;
            }
            if (blk->column_sync[i] && !_box_match_usage(box, column_use_type, column_use_type2))
                return FALSE;
        }
    }
    return TRUE;
}

int box_alloc(Box *box, Time time) {
    struct Block *blk = box->block;
    CellIdx *loc = box->loc;

    if (time >= 0)
        box->alloc_time = time;

    if (blk->stacking_axis >= 0) {
        loc[blk->stacking_axis] = BLK_USAGE_OCCUPIED(blk, loc, blk->stacking_axis);
    }

    if (loc[0] < 0 || loc[1] < 0 || loc[2] < 0)
        return ERROR_ALLOC_CELL_MISSING_LOCATION_INFO;

    if (!box_position_is_valid(box, blk, loc))
        return ERROR_INVALID_LOCATION;

    _blk_link_cell(blk, box);
    _box_adjust_and_mark_usage(blk, box, 1, TRUE);

    if (time >= 0 && box->state != BOX_STATE_PLACEHOLDER)
        box->state = BOX_STATE_ALLOCATED;

    return SUCCEED;
}

void box_store_position(Box *box, CellIdx *idx, bool new_loc) {
    Block *blk = box->block;
    if (!new_loc)
        memcpy(idx, box->loc, sizeof(CellIdx) * 3);
    _blk_top_of_stack(blk, idx);
}

int box_store(Box *box, Time time) {
    Block *blk = box->block;

    if (time >= 0 && box->state != BOX_STATE_RELOCATING)
        box->store_time = time;

    if (blk->stacking_axis >= 0)
        _box_sink(box);

    _box_adjust_and_mark_usage(blk, box, 1, FALSE);
    box->state = BOX_STATE_STORED;

    return SUCCEED;
}

int box_retrieve(Box *box, Time time) {
    Block *blk = box->block;

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

int box_place_holder(Box *box, CellIdx *new_loc) {
    Box *holder = (Box *) malloc(sizeof(Box));
    memcpy(holder, box, sizeof(Box));
    holder->state = BOX_STATE_PLACEHOLDER;
    holder->_holder_or_origin = box;

    int res;
    if (new_loc) {
        memcpy(holder->loc, new_loc, sizeof(CellIdx) * 3);
        if ((res = box_alloc(holder, -1)) != SUCCEED)
            return res;
    } else {
        _blk_unlink_cell(box->block, box);
        _blk_link_cell(holder->block, holder);
    }

    box->_holder_or_origin = holder;
    return SUCCEED;
}

int box_remove_holder(Box *box) {
    Box *holder = box->_holder_or_origin;
    int res;

    if ((res = box_retrieve(holder, -1)) != SUCCEED)
        return res;

    box_destroy(box->_holder_or_origin);
    free(box->_holder_or_origin);

    box->_holder_or_origin = NULL;
    return SUCCEED;
}

int box_realloc(Box *box, Time time, CellIdx *new_loc) {
    box_place_holder(box, NULL);

    memcpy(box->loc, new_loc, sizeof(CellIdx) * 3);
    int res = box_alloc(box, -1);
    return res;
}

void box_relocate_position(Box *box, CellIdx *loc) {
    return box_store_position(box->_holder_or_origin, loc, 0);
}

int box_relocate_alloc(Box *box, Time time, CellIdx *new_loc) {
    return box_place_holder(box, new_loc);
}

int box_relocate_retrieve(Box *box, Time time) {
    int res;
    if ((res = box_retrieve(box, -1)) != SUCCEED) {
        assert(res == SUCCEED);
        return res;
    }
//    printf("%s relocating\n", box->id);
    box->state = BOX_STATE_RELOCATING;
    return SUCCEED;
}

int box_relocate_store(Box *box, Time time) {
    assert(box->_holder_or_origin);
    memcpy(box->loc, box->_holder_or_origin->loc, sizeof(CellIdx) * 3);
    box_remove_holder(box);
    box_alloc(box, -1);
    return box_store(box, -1);
}

