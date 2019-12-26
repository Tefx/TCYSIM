//
// Created by tefx on 10/21/19.
//

#ifndef LIBTCY_DEFINE_H
#define LIBTCY_DEFINE_H

#include <inttypes.h>
#include <stdio.h>

#ifdef _MSC_VER
#define DLLEXPORT __declspec(dllexport)
#else
#define DLLEXPORT
#endif

#ifndef NULL
#define NULL 0
#endif

#ifndef TRUE
#define TRUE 1
#define FALSE 0
#endif

#ifndef bool
#define bool int
#endif

#define BOX_ID_LEN_LIMIT 32
#define TIME_INF 31536000

typedef enum {
    BOX_SIZE_TWENTY,
    BOX_SIZE_FORTY,
} BoxSize;

typedef enum {
    BOX_STATE_INITIAL = 0,
    BOX_STATE_ALLOCATED = 1,
    BOX_STATE_STORING = 2,
    BOX_STATE_STORED = 3,
    BOX_STATE_RESHUFFLING = 4,
    BOX_STATE_RETRIEVING = 5,
    BOX_STATE_RETRIEVED = 6,
} BoxState;

typedef enum {
    SLOT_USAGE_FREE,
    SLOT_USAGE_TWENTY_ONLY,
    SLOT_USAGE_FORTY_ONLY,
    SLOT_USAGE_FORTY_ONLY_END,
} SlotUsage;

typedef int64_t Time;
typedef int32_t CellIdx;
typedef struct Block Block;

typedef struct {
    char id[BOX_ID_LEN_LIMIT];
    BoxSize size;
    BoxState state;
    Time alloc_time, store_time, retrieval_time;
    CellIdx loc[3];
    Block *block;
    void* _self;
} Box;

typedef Box *Cell;

typedef struct Block {
    CellIdx spec[3];
    bool column_sync[3];
    SlotUsage *column_use_type[3];
    CellIdx *column_usage[3];
    CellIdx *column_usage_occupied[3];
    CellIdx cell_num;
    Cell *cells;
    int stacking_axis;
    int box_orientation;
    bool *lock_map;
    void* _self;
} Block;

#endif //LIBTCY_DEFINE_H
