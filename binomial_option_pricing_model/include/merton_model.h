#pragma once
#include <vector>
#include <cmath>
#include "black_scholes.h" 
struct MJDResult {
    double price;
    double delta;
    double gamma;
    double theta;
    double vega;
    double rho;
};

class Merton {
public:
    Merton() = default;

    MJDResult calculate(double S, double K, double T, double r, double sigma, 
                        double lambda, double mu_j, double delta_j, bool is_call);
};