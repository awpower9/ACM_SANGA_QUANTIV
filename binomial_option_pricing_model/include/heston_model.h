#pragma once
#include <complex>
#include <vector>

struct HestonResult {
    double price;
    double delta;
    double gamma;
    double theta;
    double vega;
    double rho;
};

class Heston {
public:
    Heston() = default;

    /**
     * @param S Spot price
     * @param K Strike price
     * @param T Time to maturity
     * @param r Risk-free rate
     * @param kappa Mean reversion speed
     * @param theta Long-term variance
     * @param xi Volatility of volatility
     * @param rho Correlation between price and volatility
     * @param v0 Initial variance
     * @param is_call True for call, false for put
     */
    HestonResult calculate(double S, double K, double T, double r, 
                           double kappa, double theta, double xi, double rho, 
                           double v0, bool is_call);
};
