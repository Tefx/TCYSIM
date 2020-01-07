//
// Created by tefx on 10/21/19.
//

#include "block.h"
#include "error.h"
#include "box.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>

void block_init(Block *blk, const CellIdx *spec, int box_orientation, int stacking_axis, const bool *axis_need_sync) {
    blk->cell_num = spec[0] * spec[1] * spec[2];
    blk->cells = (Cell *) malloc(sizeof(Cell) * blk->cell_num);
    blk->box_orientation = box_orientation;
    blk->stacking_axis = stacking_axis;

    memset(blk->cells, 0, sizeof(Cell) * blk->cell_num);
    memcpy(blk->spec, spec, sizeof(CellIdx) * 3);
    memcpy(blk->column_sync, axis_need_sync, sizeof(bool) * 3);

    for (int i = 0; i < 3; ++i) {
        CellIdx num = blk->cell_num / spec[i];
        if (axis_need_sync[i]) {
            blk->column_use_type[i] = (SlotUsage *) malloc(sizeof(SlotUsage) * num);
            for (int j = 0; j < num; ++j)
                blk->column_use_type[i][j] = SLOT_USAGE_FREE;
        } else {
            blk->column_use_type[i] = NULL;
        }
        blk->column_usage[i] = (CellIdx *) malloc(sizeof(CellIdx) * num);
        blk->column_usage_occupied[i] = (CellIdx *) malloc(sizeof(CellIdx) * num);
        memset(blk->column_usage[i], 0, sizeof(CellIdx) * num);
        memset(blk->column_usage_occupied[i], 0, sizeof(CellIdx) * num);
    }

    CellIdx stack_num = 1;
    for (int i = 0; i < 3; ++i)
        if (i != stacking_axis)
            stack_num *= spec[i];
    blk->lock_map = malloc(sizeof(bool) * stack_num);
    memset(blk->lock_map, 0, sizeof(bool) * stack_num);
}

void block_destroy(Block *blk) {
    free(blk->cells);
    for (int i = 0; i < 3; ++i) {
        if (blk->column_use_type[i]) free(blk->column_use_type[i]);
        free(blk->column_usage_occupied[i]);
        free(blk->column_usage[i]);
    }
}

inline CellIdx _blk_clmn_idx(Block *blk, const CellIdx *loc, int along) {
    if (along == 2) {
        return loc[1] + loc[0] * blk->spec[1];
    } else if (along == 1) {
        return loc[2] + loc[0] * blk->spec[2];
    } else if (along == 0) {
        return loc[2] + loc[1] * blk->spec[2];
    } else {
        return -1;
    }
}

inline CellIdx _blk_cell_idx(Block *blk, const CellIdx *loc) {
    return (loc[0] * blk->spec[1] + loc[1]) * blk->spec[2] + loc[2];
}

void _blk_link_cell(Block *blk, Box *box) {
    blk->cells[_blk_cell_idx(blk, box->loc)] = box;
    if (box->size == BOX_SIZE_FORTY) {
        box->loc[blk->box_orientation]++;
        blk->cells[_blk_cell_idx(blk, box->loc)] = box;
        box->loc[blk->box_orientation]--;
    }
}

void _blk_unlink_cell(Block *blk, Box *box) {
    blk->cells[_blk_cell_idx(blk, box->loc)] = NULL;
    if (box->size == BOX_SIZE_FORTY) {
        box->loc[blk->box_orientation]++;
        blk->cells[_blk_cell_idx(blk, box->loc)] = NULL;
        box->loc[blk->box_orientation]--;
    }
}

Box *_blk_neighbor_box(Block *blk, Box *box, int along, bool inc) {
    CellIdx loc2[3];
    for (int i = 0; i < 3; i++) loc2[i] = box->loc[i];

    if (inc && along == blk->box_orientation && box->size == BOX_SIZE_FORTY)
        loc2[along] += 2;
    else if (inc)
        loc2[along] += 1;
    else
        loc2[along] -= 1;
    if (loc2[along] >= blk->spec[along] || loc2[along] < 0)
        return NULL;
    else {
        return blk->cells[_blk_cell_idx(blk, loc2)];
    }
}

int block_usage(Block *blk, const CellIdx *loc, bool include_occupied) {
    int dimension = 3;
    int count = 0;
    CellIdx tmp_loc[3];
    CellIdx **usages;

    for (int i = 0; i < 3; i++) tmp_loc[i] = loc[i];

    if (include_occupied)
        usages = blk->column_usage_occupied;
    else
        usages = blk->column_usage;

    for (int i = 0; i < 3; ++i)
        if (loc[i] >= 0)
            dimension--;

    if (dimension == 1) {
        for (int i = 0; i < 3; ++i)
            if (loc[i] < 0) {
                count = usages[i][_blk_clmn_idx(blk, loc, i)];
                assert(count >= 0);
                break;
            }
    } else if (dimension == 2) {
        for (int i = 0; i < 3; ++i)
            if (loc[i] >= 0) {
                int k = (i + 1) % 3;
                for (int j = 0; j < blk->spec[k]; ++j) {
                    tmp_loc[k] = j;
                    count += usages[(k + 1) % 3][_blk_clmn_idx(blk, tmp_loc, (k + 1) % 3)];
                }
                break;
            }
    } else if (dimension == 3) {
        for (tmp_loc[0] = 0; tmp_loc[0] < blk->spec[0]; ++tmp_loc[0])
            for (tmp_loc[1] = 0; tmp_loc[1] < blk->spec[1]; ++tmp_loc[1])
                count += usages[2][_blk_clmn_idx(blk, tmp_loc, 2)];
    }
    return count;
}

inline Box *block_box_at(Block *blk, const CellIdx *idx) {
    Box *res = blk->cells[_blk_cell_idx(blk, idx)];
    return res;
}

Box *block_top_box(Block *blk, const CellIdx *idx, int along) {
    CellIdx tmp_idx[3];

    for (int i = 0; i < 3; i++) tmp_idx[i] = idx[i];

    tmp_idx[along] = blk->column_usage[along][_blk_clmn_idx(blk, idx, along)] - 1;
    return block_box_at(blk, tmp_idx);
}

void _blk_top_of_stack(Block *blk, CellIdx *idx) {
    int along = blk->stacking_axis;
    if (along >= 0)
        idx[along] = blk->column_usage[along][_blk_clmn_idx(blk, idx, along)];
}

CellIdx blk_stack_hash(Block *blk, const CellIdx *idx) {
    CellIdx map_idx = 0;
    CellIdx k = 1;
    for (int i = 2; i >= 0; --i)
        if (i != blk->stacking_axis) {
            map_idx = idx[i] * k;
            k *= blk->spec[i];
        }
    return map_idx;
}

int block_column_state(Block *blk, const CellIdx* idx, int axis){
    return blk->column_use_type[axis][_blk_clmn_idx(blk, idx, axis)];
}

void block_lock(Block *blk, const CellIdx* idx) {
    CellIdx map_idx = blk_stack_hash(blk, idx);
    blk->lock_map[map_idx] = TRUE;
}

void block_unlock(Block *blk, const CellIdx* idx) {
    CellIdx map_idx = blk_stack_hash(blk, idx);
    blk->lock_map[map_idx] = FALSE;
}

bool block_is_locked(Block *blk, const CellIdx* idx){
    CellIdx map_idx = blk_stack_hash(blk, idx);
    return blk->lock_map[map_idx];
}
