//
// Created by tefx on 10/23/19.
//

#ifndef TCY_PATH_H
#define TCY_PATH_H

#include "define.h"

typedef struct {
    Time time;
    double coord;
    void* other;
} PathKeyFrame;

typedef struct PathFrameChunk{
    int num;
    PathKeyFrame* frames;
    struct PathFrameChunk* next;
} PathFrameChunk;

typedef struct{
    int chunk_size;
    PathFrameChunk* chunks;
    PathFrameChunk* last_chunk;
    double max, min;
} PathTrace;

DLLEXPORT void pathtrace_init(PathTrace *pt, int chunk_size);
DLLEXPORT void pathtrace_destroy(PathTrace *pt);
DLLEXPORT void pathtrace_append_frame(PathTrace *pt, Time time, double coord, void *other);
DLLEXPORT bool pathtrace_intersect_test_with_clearance(PathTrace *pt0, PathTrace *pt1, double clearance, double shift);
DLLEXPORT void pathtrace_boundary(PathTrace* pt, double* pmax, double* pmin);

#endif //TCY_PATH_H
