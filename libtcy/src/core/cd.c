//
// Created by tefx on 10/23/19.
//

#include "define.h"
#include "cd.h"

#include <math.h>

static inline float cross_product(float x1, float y1, float x2, float y2) {
    return x1 * y2 - x2 * y1;
}

static inline bool cross_test(float xa, float ya, float xb, float yb, float xc, float yc, float xd, float yd) {
    if (xa == xb || xc == xd)
        return ya == yc;
    float p_ab_ac = cross_product(xb - xa, yb - ya, xc - xa, yc - ya);
    float p_ab_ad = cross_product(xb - xa, yb - ya, xd - xa, yd - ya);
    float p_cd_ca = cross_product(xd - xc, yd - yc, xa - xc, ya - yc);
    float p_cd_cb = cross_product(xd - xc, yd - yc, xb - xc, yb - yc);
    return p_ab_ac * p_ab_ad <= 0 && p_cd_ca * p_cd_cb <= 0;
}

bool cross_test_with_clearance(float xa, float ya, float xb, float yb, float xc, float yc, float xd, float yd,
                               float clearance) {
    if (ya >= yc)
        return cross_test(xa, ya - clearance, xb, yb - clearance, xc, yc, xd, yd);
    else
        return cross_test(xa, ya + clearance, xb, yb + clearance, xc, yc, xd, yd);
}

static inline float min_shift(float x1, float y1, float x2, float y2, float x3, float y3, float x4, float y4) {
    float d = fmaxf(x1, x2) - fminf(x3, x4);
    float k, d1;
    if (y1 != y2) {
        k = (x1 - x2) / (y1 - y2);
        d1 = x1 - x3 + k * (-y1 + y3);
        if (0 < d1 && d1 < d)
            d = d1;
        d1 = x1 - x4 + k * (-y1 + y4);
        if (0 < d1 && d1 < d)
            d = d1;
    }
    if (y3 != y4) {
        k = (x3 - x4) / (y3 - y4);
        d1 = x1 - x3 - k * (y1 - y3);
        if (0 < d1 && d1 < d)
            d = d1;
        d1 = x2 - x3 - k * (y2 - y3);
        if (0 < d1 && d1 < d)
            d = d1;
    }
    return d + 1;
}

float min_shift_with_clearance(float xa, float ya, float xb, float yb, float xc, float yc, float xd, float yd,
                               float clearance) {
    float res = 0;
    res = fmaxf(res, min_shift(xa, ya + clearance, xb, yb + clearance, xc, yc, xd, yd));
    res = fmaxf(res, min_shift(xa, ya - clearance, xb, yb - clearance, xc, yc, xd, yd));
    res = fmaxf(res, min_shift(xa, ya + clearance, xa, ya - clearance, xc, yc, xd, yd));
    res = fmaxf(res, min_shift(xb, yb + clearance, xb, yb - clearance, xc, yc, xd, yd));
    return res;
}