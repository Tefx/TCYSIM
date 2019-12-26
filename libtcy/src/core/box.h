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
DLLEXPORT int box_reshuffle(Box *box, int32_t *new_loc);
DLLEXPORT bool box_location_is_valid(Box* box, Block* blk, CellIdx * loc);


#endif //LIBTCY_BOX_H
