#define _USE_MATH_DEFINES
#include <cmath>
#include "../include/merton_model.h"
#include <iostream>
#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif



MJDResult Merton::calculate(double S, double K, double T, double r, double sigma, 
                                               double lambda, double mu_j, double delta_j, bool is_call) {
    MJDResult res = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
    
    // Safety check
    if (T <= 0 || S <= 0 || K <= 0) return res;

    BlackScholes bsm; // We use the existing engine
    
    // Pre-calculate jump drift correction
    // k is the expected percentage jump size
    double k = std::exp(mu_j + 0.5 * delta_j * delta_j) - 1.0;
    
    // The rate 'r' in BSM is adjusted to remove the expected jump drift
    double lambda_prime = lambda * (1.0 + k);
    
    //  sum  of the first 15 terms
    int max_jumps = 15; 
    
    for (int n = 0; n < max_jumps; ++n) {
        // 1. Calculate Probability of exactly 'n' jumps (Poisson Distribution)
        // P(n) = (e^(-lambda*T) * (lambda*T)^n) / n!
        double num = std::exp(-lambda_prime * T) * std::pow(lambda_prime * T, n);
        double den = 1.0; 
        for(int i=1; i<=n; ++i) den *= i; // Factorial
        double weight = num / den;

        // 2. Adjust parameters for this specific 'n'
        // New variance = sigma^2 + (n * delta_j^2) / T
        double sigma_n = std::sqrt(sigma * sigma + (n * delta_j * delta_j) / T);
        
        // New rate = r - lambda*k + (n * log(1+k)) / T
        double r_n = r - lambda * k + (n * std::log(1.0 + k)) / T;

        double d1 = (std::log(S / K) + (r_n + 0.5 * sigma_n * sigma_n) * T) / (sigma_n * std::sqrt(T));
        double d2 = d1 - sigma_n * std::sqrt(T);
        double Nd1 = 0.5 * (1.0 + std::erf(d1 / std::sqrt(2.0)));
        double Nd2 = 0.5 * (1.0 + std::erf(d2 / std::sqrt(2.0)));
        double pdf_d1 = (1.0 / std::sqrt(2.0 * M_PI)) * std::exp(-0.5 * d1 * d1);

        double price_n = 0;
        double delta_n = 0;
        
        if (is_call) {
            price_n = S * Nd1 - K * std::exp(-r_n * T) * Nd2;
            delta_n = Nd1;
        } else {
            price_n = K * std::exp(-r_n * T) * (1.0 - Nd2) - S * (1.0 - Nd1);
            delta_n = Nd1 - 1.0;
        }
        
        // Add weighted contribution to result
        res.price += weight * price_n;
        res.delta += weight * delta_n;
        
        // Approximate other Greeks (Gamma, Vega) based on main weight
        if (n == 0) {
             res.gamma += weight * (pdf_d1 / (S * sigma_n * std::sqrt(T)));
             res.vega  += weight * (S * std::sqrt(T) * pdf_d1) / 100.0;
        }
    }
    
    return res;
}