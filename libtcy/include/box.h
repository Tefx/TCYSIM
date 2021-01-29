//
// Created by tefx on 10/22/19.
//

#ifndef LIBTCY_BOX_H
#define LIBTCY_BOX_H

#include "define.h"
#include "block.h"

DLLEXPORT void box_init(Box_TCY *box, char *box_id, BoxSize_TCY size);

DLLEXPORT void box_destroy(Box_TCY *box);

DLLEXPORT int box_alloc(Box_TCY *box, Time_TCY time);

DLLEXPORT int box_store(Box_TCY *box, Time_TCY time);

DLLEXPORT int box_retrieve(Box_TCY *box, Time_TCY time);

DLLEXPORT void box_store_position(Box_TCY *box, CellIdx_TCY *idx, bool new_loc);

DLLEXPORT int box_place_holder(Box_TCY *box, Block_TCY *block, CellIdx_TCY *new_loc);

DLLEXPORT int box_remove_holder(Box_TCY *box);

DLLEXPORT int box_cancel_and_realloc(Box_TCY* box, Block_TCY *blk, CellIdx_TCY* new_loc);

DLLEXPORT int box_realloc(Box_TCY *box, Time_TCY time, Block_TCY *blk, CellIdx_TCY *new_loc);

DLLEXPORT void box_relocate_position(Box_TCY *box, Block_TCY ** blk, CellIdx_TCY *loc);

DLLEXPORT int box_relocate_alloc(Box_TCY *box, Time_TCY time, Block_TCY* blk, CellIdx_TCY *new_loc);

DLLEXPORT int box_relocate_retrieve(Box_TCY *box, Time_TCY time);

DLLEXPORT int box_relocate_store(Box_TCY *box, Time_TCY time);


#endif //LIBTCY_BOX_H
