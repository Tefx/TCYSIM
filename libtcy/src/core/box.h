//
// Created by tefx on 10/22/19.
//

#ifndef LIBTCY_BOX_H
#define LIBTCY_BOX_H

#include "define.h"
#include "block.h"

DLLEXPORT void box_init(Box *box, char *box_id, BoxSize size);

DLLEXPORT void box_destroy(Box *box);

DLLEXPORT int box_alloc(Box *box, Time time);

DLLEXPORT int box_store(Box *box, Time time);

DLLEXPORT int box_retrieve(Box *box, Time time);

DLLEXPORT bool box_position_is_valid(Box *box, Block *blk, CellIdx *loc);

DLLEXPORT void box_store_position(Box *box, CellIdx *idx, bool new_loc);

DLLEXPORT int box_place_holder(Box *box, CellIdx *new_loc);

DLLEXPORT int box_remove_holder(Box *box);

DLLEXPORT int box_realloc(Box *box, Time time, CellIdx *new_loc);

DLLEXPORT void box_relocate_position(Box *box, CellIdx *loc);

DLLEXPORT int box_relocate_alloc(Box *box, Time time, CellIdx *new_loc);

DLLEXPORT int box_relocate_retrieve(Box *box, Time time);

DLLEXPORT int box_relocate_store(Box *box, Time time);


#endif //LIBTCY_BOX_H
