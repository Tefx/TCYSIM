//
// Created by tefx on 10/21/19.
//

#ifndef LIBTCY_BLOCK_H
#define LIBTCY_BLOCK_H

#include "define.h"

#define BLK_USAGE(blk, loc, axis) ((blk)->column_usage[(axis)][_blk_clmn_idx((blk), (loc), (axis))])
#define BLK_USAGE_OCCUPIED(blk, loc, axis) ((blk)->column_usage_occupied[(axis)][_blk_clmn_idx((blk), (loc), (axis))])
#define BLK_USE_TYPE(blk, loc, axis) ((blk)->column_use_type[(axis)][_blk_clmn_idx((blk), (loc), (axis))])

CellIdx _blk_clmn_idx(Block *blk, const CellIdx *loc, int along);

CellIdx _blk_cell_idx(Block *blk, const CellIdx *loc);

void _blk_link_cell(Block *blk, Box *box);

void _blk_unlink_cell(Block *blk, Box *box);

Box *_blk_neighbor_box(Block *blk, Box *box, int along, bool inc);

void _blk_top_of_stack(Block *blk, CellIdx *idx);

DLLEXPORT void
block_init(Block *blk, const CellIdx *spec, int box_orientation, int stacking_axis, const bool *axis_need_sync);

DLLEXPORT void block_destroy(Block *blk);

DLLEXPORT int block_usage(Block *blk, const CellIdx *loc, bool include_occupied);

DLLEXPORT Box *block_box_at(Block *blk, const CellIdx *idx);

DLLEXPORT Box *block_top_box(Block *blk, const CellIdx *idx, int along);

DLLEXPORT CellIdx blk_stack_hash(Block *blk, const CellIdx *idx);

DLLEXPORT void block_lock(Block *blk, const CellIdx *idx);

DLLEXPORT void block_unlock(Block *blk, const CellIdx *idx);

DLLEXPORT bool block_is_locked(Block *blk, const CellIdx *idx);

DLLEXPORT int block_column_state(Block *blk, const CellIdx *idx, int axis);

#endif //LIBTCY_BLOCK_H
