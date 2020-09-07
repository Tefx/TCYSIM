//
// Created by tefx on 10/21/19.
//

#ifndef LIBTCY_DEFINE_H
#define LIBTCY_DEFINE_H

#include <inttypes.h>
#include <stdio.h>

#ifdef _MSC_VER
    #if defined (DLL_EXPORT)
        #define DLLEXPORT __declspec(dllexport)
    #else
        #define DLLEXPORT
    #endif
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
#define TIME_INF 315360000

typedef enum {
    BOX_SIZE_TWENTY = 0,
    BOX_SIZE_FORTY = 1,
} BoxSize_TCY;

typedef enum {
    BOX_STATE_INITIAL = 0,
    BOX_STATE_ALLOCATED = 1,
    BOX_STATE_STORING = 2,
    BOX_STATE_STORED = 3,
    BOX_STATE_RELOCATING = 4,
    BOX_STATE_RETRIEVING = 5,
    BOX_STATE_RETRIEVED = 6,
    BOX_STATE_PLACEHOLDER = 7,
} BoxState_TCY;

typedef enum {
    SLOT_USAGE_FREE = 0,
    SLOT_USAGE_TWENTY_ONLY = 1,
    SLOT_USAGE_FORTY_ONLY = 2,
    SLOT_USAGE_FORTY_ONLY_END = 3,
} SlotUsage_TCY;

typedef double Time_TCY;
typedef int32_t CellIdx_TCY;
typedef struct Block_TCY Block_TCY;

typedef struct Box_TCY {
    char id[BOX_ID_LEN_LIMIT];
    BoxSize_TCY size;
    BoxState_TCY state;
    Time_TCY alloc_time, store_time, retrieval_time;
    CellIdx_TCY loc[3];
    Block_TCY *block;
    void *_self;
    struct Box_TCY *_holder_or_origin;
    int64_t _hash;
} Box_TCY;

typedef Box_TCY *Cell_TCY;

typedef struct Block_TCY {
    CellIdx_TCY spec[3];
    bool column_sync[3];
    SlotUsage_TCY *column_use_type[3];
    CellIdx_TCY *column_usage[3];
    CellIdx_TCY *column_usage_occupied[3];
    CellIdx_TCY cell_num;
    Cell_TCY *cells;
    int stacking_axis;
    int box_orientation;
    bool *lock_map;
    void *_self;
} Block_TCY;


int flt(double x, double y);

int feq(double x, double y);

int fne(double x, double y);

#define MAX(a,b) ((a) > (b) ? a : b)
#define MIN(a,b) ((a) < (b) ? a : b)

#endif //LIBTCY_DEFINE_H
