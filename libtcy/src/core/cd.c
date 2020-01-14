//
// Created by tefx on 10/23/19.
//

#include "define.h"
#include "cd.h"

#include <math.h>

static inline double cross_product(double x1, double y1, double x2, double y2) {
    return x1 * y2 - x2 * y1;
}

static inline bool cross_test(double xa, double ya, double xb, double yb, double xc, double yc, double xd, double yd) {
    if (xa == xb || xc == xd)
        return ya == yc;
    double p_ab_ac = cross_product(xb - xa, yb - ya, xc - xa, yc - ya);
    double p_ab_ad = cross_product(xb - xa, yb - ya, xd - xa, yd - ya);
    double p_cd_ca = cross_product(xd - xc, yd - yc, xa - xc, ya - yc);
    double p_cd_cb = cross_product(xd - xc, yd - yc, xb - xc, yb - yc);
    return p_ab_ac * p_ab_ad <= 0 && p_cd_ca * p_cd_cb <= 0;
}

bool cross_test_with_clearance(double xa, double ya, double xb, double yb, double xc, double yc, double xd, double yd,
                               double clearance) {
    if (ya >= yc)
        return cross_test(xa, ya - clearance, xb, yb - clearance, xc, yc, xd, yd);
    else
        return cross_test(xa, ya + clearance, xb, yb + clearance, xc, yc, xd, yd);
}

static inline double min_shift(double x1, double y1, double x2, double y2, double x3, double y3, double x4, double y4) {
    double d = fmaxf(x1, x2) - fminf(x3, x4);
    double k, d1;
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

double min_shift_with_clearance(double xa, double ya, double xb, double yb, double xc, double yc, double xd, double yd,
                               double clearance) {
    double res = 0;
    res = fmaxf(res, min_shift(xa, ya + clearance, xb, yb + clearance, xc, yc, xd, yd));
    res = fmaxf(res, min_shift(xa, ya - clearance, xb, yb - clearance, xc, yc, xd, yd));
    res = fmaxf(res, min_shift(xa, ya + clearance, xa, ya - clearance, xc, yc, xd, yd));
    res = fmaxf(res, min_shift(xb, yb + clearance, xb, yb - clearance, xc, yc, xd, yd));
    return res;
}