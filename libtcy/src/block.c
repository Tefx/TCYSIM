//
// Created by tefx on 10/21/19.
//

#include "../include/define.h"
#include "../include/block.h"
#include "../include/error.h"
#include "../include/box.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>

void block_init(Block_TCY *blk, const CellIdx_TCY *spec, int box_orientation, int stacking_axis,
                const bool *axis_need_sync) {
    blk->cell_num = spec[0] * spec[1] * spec[2];
    blk->cells = (Cell_TCY *) malloc(sizeof(Cell_TCY) * blk->cell_num);
    blk->box_orientation = box_orientation;
    blk->stacking_axis = stacking_axis;

    memset(blk->cells, 0, sizeof(Cell_TCY) * blk->cell_num);
    memcpy(blk->spec, spec, sizeof(CellIdx_TCY) * 3);
    memcpy(blk->column_sync, axis_need_sync, sizeof(bool) * 3);

    for (int i = 0; i < 3; ++i) {
        CellIdx_TCY num = blk->cell_num / spec[i];
        if (axis_need_sync[i]) {
            blk->column_use_type[i] = (SlotUsage_TCY *) malloc(sizeof(SlotUsage_TCY) * num);
            for (int j = 0; j < num; ++j)
                blk->column_use_type[i][j] = SLOT_USAGE_FREE;
        } else {
            blk->column_use_type[i] = NULL;
        }
        blk->column_usage[i] = (CellIdx_TCY *) malloc(sizeof(CellIdx_TCY) * num);
        blk->column_usage_occupied[i] = (CellIdx_TCY *) malloc(sizeof(CellIdx_TCY) * num);
        memset(blk->column_usage[i], 0, sizeof(CellIdx_TCY) * num);
        memset(blk->column_usage_occupied[i], 0, sizeof(CellIdx_TCY) * num);
    }

    CellIdx_TCY stack_num = 1;
    for (int i = 0; i < 3; ++i)
        if (i != stacking_axis)
            stack_num *= spec[i];
    blk->lock_map = malloc(sizeof(bool) * stack_num);
    memset(blk->lock_map, 0, sizeof(bool) * stack_num);
}

void block_destroy(Block_TCY *blk) {
    free(blk->cells);
    for (int i = 0; i < 3; ++i) {
        if (blk->column_use_type[i]) free(blk->column_use_type[i]);
        free(blk->column_usage_occupied[i]);
        free(blk->column_usage[i]);
    }
}

CellIdx_TCY _blk_clmn_idx(Block_TCY *blk, const CellIdx_TCY *loc, int along) {
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

inline CellIdx_TCY _blk_cell_idx(Block_TCY *blk, const CellIdx_TCY *loc) {
    return (loc[0] * blk->spec[1] + loc[1]) * blk->spec[2] + loc[2];
}

void _blk_link_cell(Block_TCY *blk, Box_TCY *box) {
    blk->cells[_blk_cell_idx(blk, box->loc)] = box;
    if (box->size == BOX_SIZE_FORTY) {
        box->loc[blk->box_orientation]++;
        blk->cells[_blk_cell_idx(blk, box->loc)] = box;
        box->loc[blk->box_orientation]--;
    }
}

void _blk_unlink_cell(Block_TCY *blk, Box_TCY *box) {
    blk->cells[_blk_cell_idx(blk, box->loc)] = NULL;
    if (box->size == BOX_SIZE_FORTY) {
        box->loc[blk->box_orientation]++;
        blk->cells[_blk_cell_idx(blk, box->loc)] = NULL;
        box->loc[blk->box_orientation]--;
    }
}

Box_TCY *_blk_neighbor_box(Block_TCY *blk, Box_TCY *box, int along, bool inc) {
    CellIdx_TCY loc2[3];
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

int block_usage(Block_TCY *blk, const CellIdx_TCY *loc, bool include_occupied) {
    int dimension = 3;
    int count = 0;
    CellIdx_TCY tmp_loc[3];
    CellIdx_TCY **usages;

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
                if (count < 0)
                    printf("(%d, %d, %d) %d %d\n", loc[0], loc[1], loc[2], i, include_occupied);
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

inline Box_TCY *block_box_at(Block_TCY *blk, const CellIdx_TCY *idx) {
    Box_TCY *res = blk->cells[_blk_cell_idx(blk, idx)];
    return res;
}

Box_TCY *block_top_box(Block_TCY *blk, const CellIdx_TCY *idx, int along) {
    CellIdx_TCY tmp_idx[3];

    for (int i = 0; i < 3; i++) tmp_idx[i] = idx[i];

    tmp_idx[along] = blk->column_usage[along][_blk_clmn_idx(blk, idx, along)] - 1;
    return block_box_at(blk, tmp_idx);
}

void _blk_top_of_stack(Block_TCY *blk, CellIdx_TCY *idx) {
    int along = blk->stacking_axis;
    if (along >= 0)
        idx[along] = blk->column_usage[along][_blk_clmn_idx(blk, idx, along)];
}

CellIdx_TCY blk_stack_hash(Block_TCY *blk, const CellIdx_TCY *idx) {
    CellIdx_TCY map_idx = 0;
    CellIdx_TCY k = 1;
    for (int i = 2; i >= 0; --i)
        if (i != blk->stacking_axis) {
            map_idx += idx[i] * k;
            k *= blk->spec[i];
        }
    return map_idx;
}

SlotUsage_TCY block_column_state(Block_TCY *blk, const CellIdx_TCY *idx, int axis) {
    return blk->column_use_type[axis][_blk_clmn_idx(blk, idx, axis)];
}

void block_lock(Block_TCY *blk, const CellIdx_TCY *idx) {
    CellIdx_TCY map_idx = blk_stack_hash(blk, idx);
    blk->lock_map[map_idx] = TRUE;
}

void block_unlock(Block_TCY *blk, const CellIdx_TCY *idx) {
    CellIdx_TCY map_idx = blk_stack_hash(blk, idx);
    blk->lock_map[map_idx] = FALSE;
}

bool block_is_locked(Block_TCY *blk, const CellIdx_TCY *idx) {
    CellIdx_TCY map_idx = blk_stack_hash(blk, idx);
    return blk->lock_map[map_idx];
}

static inline bool _compare_usage(BoxSize_TCY box_size, SlotUsage_TCY usage, SlotUsage_TCY usage2) {
    if (usage == SLOT_USAGE_FREE)
        if (box_size == BOX_SIZE_FORTY)
            return usage2 == SLOT_USAGE_FREE;
        else
            return TRUE;
    else if (usage == SLOT_USAGE_TWENTY_ONLY)
        return box_size == BOX_SIZE_TWENTY;
    else if (usage == SLOT_USAGE_FORTY_ONLY)
        return box_size == BOX_SIZE_FORTY;
    else
        return FALSE;
}

bool block_position_is_valid_for_size(Block_TCY *blk, CellIdx_TCY *loc, BoxSize_TCY box_size) {
    SlotUsage_TCY clmn_ut, clmn_ut2 = SLOT_USAGE_FREE;
    if (box_size == BOX_SIZE_FORTY && loc[blk->box_orientation] > blk->spec[blk->box_orientation] - 2)
        return FALSE;
    for (int i = 0; i < 3; ++i) {
        if (loc[i] >= blk->spec[i]) {
//            printf("%d %d %d\n", i, loc[i], blk->spec[i]);
            return FALSE;
        }
        if (blk->column_use_type[i] && blk->column_sync[i]) {
            clmn_ut = blk->column_use_type[i][_blk_clmn_idx(blk, loc, i)];
            if (box_size == BOX_SIZE_FORTY) {
                loc[blk->box_orientation]++;
                clmn_ut2 = blk->column_use_type[i][_blk_clmn_idx(blk, loc, i)];
                loc[blk->box_orientation]--;
            }
            if (!_compare_usage(box_size, clmn_ut, clmn_ut2)) {
//                printf("%p %d\n", blk->column_use_type[i], blk->column_sync[i]);
                return FALSE;
            }
        }
    }
    return TRUE;
}

static inline int _other_axes(int axis, int *a0, int *a1) {
    if (axis == 0) {
        *a0 = 1, *a1 = 2;
    } else if (axis == 1) {
        *a0 = 0, *a1 = 2;
    } else if (axis == 2) {
        *a0 = 0, *a1 = 1;
    } else {
        return 1;
    }
    return 0;
}

int block_all_column_usages(Block_TCY *blk, int axis, bool include_occupied, const int *avail, int *results) {
    CellIdx_TCY tmp_loc[3], clmn_idx;
    CellIdx_TCY a0, a1;
    CellIdx_TCY **usages;

    if (include_occupied)
        usages = blk->column_usage_occupied;
    else
        usages = blk->column_usage;

    if (_other_axes(axis, &a0, &a1)) return -1;

    for (int i = 0; i < blk->spec[a0]; ++i) {
        if ((!avail) || avail[i]) {
            tmp_loc[a0] = i;
            for (int j = 0; j < blk->spec[a1]; ++j) {
                tmp_loc[a1] = j;
                clmn_idx = _blk_clmn_idx(blk, tmp_loc, axis);
                results[clmn_idx] = usages[axis][clmn_idx];
            }
        }
    }

    return 0;
}

int block_all_slot_usages(Block_TCY *blk, int norm_axis, bool include_occupied, const int *avail, int *results) {
    CellIdx_TCY tmp_loc[3];
    CellIdx_TCY a0, a1;
    CellIdx_TCY **usages;

    if (include_occupied)
        usages = blk->column_usage_occupied;
    else
        usages = blk->column_usage;

    if (_other_axes(norm_axis, &a0, &a1)) return -1;

    memset(results, 0, sizeof(int) * blk->spec[norm_axis]);

    for (int i = 0; i < blk->spec[norm_axis]; ++i) {
        if (avail == NULL || avail[i]) {
            tmp_loc[norm_axis] = i;
            for (int j = 0; j < blk->spec[a0]; ++j) {
                tmp_loc[a0] = j;
                results[i] += usages[a1][_blk_clmn_idx(blk, tmp_loc, a1)];
            }
        }
    }

    return 0;
}

int block_all_slot_states(Block_TCY *blk, int norm_axis, int *results) {
    CellIdx_TCY tmp_idx[3];
    CellIdx_TCY a0, a1;

    if (_other_axes(norm_axis, &a0, &a1)) return -1;

    for (int i = 0; i < blk->spec[norm_axis]; ++i) {
        tmp_idx[norm_axis] = i;
        tmp_idx[a0] = tmp_idx[a1] = 0;
        if (blk->column_use_type[a0]) {
            tmp_idx[a1] = 0;
            results[i] = (int) blk->column_use_type[a0][_blk_clmn_idx(blk, tmp_idx, a0)];
        } else if (blk->column_use_type[a1]) {
            tmp_idx[a0] = 0;
            results[i] = (int) blk->column_use_type[a1][_blk_clmn_idx(blk, tmp_idx, a1)];
        } else
            return -2;
    }

    return 0;
}

int block_validate_all_slots_for_size(Block_TCY *blk, int norm_axis, BoxSize_TCY box_size, bool *results) {
    SlotUsage_TCY clmn_ut, clmn_ut2 = SLOT_USAGE_FREE;
    CellIdx_TCY tmp_idx[3];
    CellIdx_TCY as[2];

    if (_other_axes(norm_axis, as, as + 1)) return -1;

    memset(results, 1, sizeof(int) * blk->spec[norm_axis]);

    for (int i = 0; i < blk->spec[norm_axis]; ++i) {
        tmp_idx[norm_axis] = i;
        for (int k = 0; k < 2; k++) {
            if (blk->column_use_type[as[k]]) {
                tmp_idx[as[1 - k]] = 0;
                clmn_ut = blk->column_use_type[as[k]][_blk_clmn_idx(blk, tmp_idx, as[k])];
                if (box_size == BOX_SIZE_FORTY) {
                    tmp_idx[blk->box_orientation]++;
                    if (tmp_idx[blk->box_orientation] >= blk->spec[blk->box_orientation]) {
                        results[i] = FALSE;
                    } else {
                        clmn_ut2 = blk->column_use_type[as[k]][_blk_clmn_idx(blk, tmp_idx, as[k])];
                    }
                    tmp_idx[blk->box_orientation]--;
                }
                results[i] = results[i] && _compare_usage(box_size, clmn_ut, clmn_ut2);
            }
        }
//        if (blk->column_use_type[a0]) {
//            tmp_idx[a1] = 0;
//            clmn_ut = blk->column_use_type[a0][_blk_clmn_idx(blk, tmp_idx, a0)];
//            if (box_size == BOX_SIZE_FORTY) {
//                tmp_idx_2[a1] = 0;
//                clmn_ut2 = blk->column_use_type[a0][_blk_clmn_idx(blk, tmp_idx_2, a0)];
//            }
//            results[i] = _compare_usage(box_size, clmn_ut, clmn_ut2);
//        }
//
//        if (blk->column_use_type[a1]) {
//            tmp_idx[a0] = 0;
//            clmn_ut = blk->column_use_type[a1][_blk_clmn_idx(blk, tmp_idx, a1)];
//            if (box_size == BOX_SIZE_FORTY) {
//                tmp_idx_2[a0] = 0;
//                clmn_ut2 = blk->column_use_type[a1][_blk_clmn_idx(blk, tmp_idx_2, a1)];
//            }
//            results[i] = results[i] && _compare_usage(box_size, clmn_ut, clmn_ut2);
//        }
    }
    return 0;
}
