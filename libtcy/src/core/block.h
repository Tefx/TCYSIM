//
// Created by tefx on 10/21/19.
//

#ifndef LIBTCY_BLOCK_H
#define LIBTCY_BLOCK_H

#include "define.h"

#define BLK_USAGE(blk, loc, axis) ((blk)->column_usage[(axis)][_blk_clmn_idx((blk), (loc), (axis))])
#define BLK_USAGE_OCCUPIED(blk, loc, axis) ((blk)->column_usage_occupied[(axis)][_blk_clmn_idx((blk), (loc), (axis))])
#define BLK_USE_TYPE(blk, loc, axis) ((blk)->column_use_type[(axis)][_blk_clmn_idx((blk), (loc), (axis))])

CellIdx_TCY _blk_clmn_idx(Block_TCY *blk, const CellIdx_TCY *loc, int along);

CellIdx_TCY _blk_cell_idx(Block_TCY *blk, const CellIdx_TCY *loc);

void _blk_link_cell(Block_TCY *blk, Box_TCY *box);

void _blk_unlink_cell(Block_TCY *blk, Box_TCY *box);

Box_TCY *_blk_neighbor_box(Block_TCY *blk, Box_TCY *box, int along, bool inc);

void _blk_top_of_stack(Block_TCY *blk, CellIdx_TCY *idx);

DLLEXPORT void
block_init(Block_TCY *blk, const CellIdx_TCY *spec, int box_orientation, int stacking_axis, const bool *axis_need_sync);

DLLEXPORT void block_destroy(Block_TCY *blk);

DLLEXPORT int block_usage(Block_TCY *blk, const CellIdx_TCY *loc, bool include_occupied);

DLLEXPORT Box_TCY *block_box_at(Block_TCY *blk, const CellIdx_TCY *idx);

DLLEXPORT Box_TCY *block_top_box(Block_TCY *blk, const CellIdx_TCY *idx, int along);

DLLEXPORT CellIdx_TCY blk_stack_hash(Block_TCY *blk, const CellIdx_TCY *idx);

DLLEXPORT void block_lock(Block_TCY *blk, const CellIdx_TCY *idx);

DLLEXPORT void block_unlock(Block_TCY *blk, const CellIdx_TCY *idx);

DLLEXPORT bool block_is_locked(Block_TCY *blk, const CellIdx_TCY *idx);

DLLEXPORT SlotUsage_TCY block_column_state(Block_TCY *blk, const CellIdx_TCY *idx, int axis);

DLLEXPORT bool block_position_is_valid_for_size(Block_TCY *blk, CellIdx_TCY *loc, BoxSize_TCY box_size);

#endif //LIBTCY_BLOCK_H
