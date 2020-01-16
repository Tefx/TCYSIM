//
// Created by tefx on 1/15/20.
//

double EPSILON = 1e-3;

int flt(double x, double y){
    return x < y - EPSILON;
}

int feq(double x, double y){
    double d = x - y;
    return d > -EPSILON && d < EPSILON;
}
int fne(double x, double y){
    double d = x - y;
    return d < -EPSILON || d > EPSILON;
}
