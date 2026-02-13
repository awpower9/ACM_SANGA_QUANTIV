#define _USE_MATH_DEFINES
#include <cmath>
#include <iostream>
#include <complex>
#include <algorithm>
#include "../include/heston_model.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

using namespace std;

// Internal helper for Heston Integrand f_j(phi)
// j = 1 or 2
complex<double> heston_function(int j, complex<double> phi, double S, double K, double T, double r,
                                double kappa, double theta, double xi, double rho, double v0) {
    complex<double> i(0.0, 1.0);
    double u_j, b_j;

    if (j == 1) {
        u_j = 0.5;
        b_j = kappa - rho * xi; // Risk-neutral parameters assumed
    } else {
        u_j = -0.5;
        b_j = kappa;
    }
    
    // d_j = sqrt( (rho*xi*phi*i - b_j)^2 - xi^2 * (2*u_j*phi*i - phi^2) )
    complex<double> term1 = rho * xi * phi * i - b_j;
    complex<double> term2 = 2.0 * u_j * phi * i - phi * phi;
    complex<double> d_j = sqrt(term1 * term1 - xi * xi * term2);
    
    // g_j = (b_j - rho*xi*phi*i + d_j) / (b_j - rho*xi*phi*i - d_j)
    complex<double> top = b_j - rho * xi * phi * i + d_j;
    complex<double> bot = b_j - rho * xi * phi * i - d_j;
    complex<double> g_j = top / bot;

    // C_j = (kappa * theta / xi^2) * [ (b_j - rho*xi*phi*i + d_j)T - 2 ln(...) ]
    // Original Heston formula usually has minus before d_j in brackets? 
    // Wait, let's use the Albrecher "Little Trap" stable form to be safe.
    // Albrecher form for Pj:
    // d_j same
    // g_j = (b_j - rho*xi*phi*i - d_j) / (b_j - rho*xi*phi*i + d_j)
    // D_j = (b_j - rho*xi*phi*i - d_j)/xi^2 * (1 - e^-dt)/(1 - g e^-dt)
    // C_j = kappa*theta/xi^2 * [ (b_j - rho*xi*phi*i - d_j)T - 2 ln( (1-g e^-dt)/(1-g) ) ]
    
    // Switch to Albrecher 2007 (stable):
    g_j = (b_j - rho * xi * phi * i - d_j) / (b_j - rho * xi * phi * i + d_j);
    
    complex<double> D_func = (b_j - rho * xi * phi * i - d_j) / (xi * xi) * 
                             ((1.0 - exp(-d_j * T)) / (1.0 - g_j * exp(-d_j * T)));
                             
    complex<double> C_func = (kappa * theta / (xi * xi)) * 
                             ((b_j - rho * xi * phi * i - d_j) * T - 2.0 * log((1.0 - g_j * exp(-d_j * T)) / (1.0 - g_j)));
                             
    // F_j = exp(C + D*v0 + i*phi*ln(S))
    return exp(C_func + D_func * v0 + i * phi * log(S));
}

HestonResult Heston::calculate(double S, double K, double T, double r, 
                               double kappa, double theta, double xi, double rho, 
                               double v0, bool is_call) {
    
    HestonResult res = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
    if (T <= 0 || S <= 0 || K <= 0) return res;

    // Calculate P1 and P2
    // P_j = 0.5 + 1/pi * integral_0^inf Re[ e^(-i phi ln K) * f_j(phi) / (i phi) ] dphi
    
    auto get_prob = [&](int j) {
        auto integrand = [&](double phi) {
            if (phi < 1e-8) return 0.0; // Limit at 0 handling
            complex<double> i(0.0, 1.0);
            complex<double> f = heston_function(j, phi, S, K, T, r, kappa, theta, xi, rho, v0);
            complex<double> val = exp(-i * phi * log(K)) * f / (i * phi);
            return val.real();
        };

        // Trapezoidal integration
        double sum = 0.0;
        double a = 1e-7; // Avoid 0
        double b = 200.0; // Extend range
        int n = 2000;
        double h = (b - a) / n;
        
        sum = 0.5 * (integrand(a) + integrand(b));
        for (int k = 1; k < n; k++) {
            sum += integrand(a + k * h);
        }
        return 0.5 + (1.0 / M_PI) * sum * h;
    };

    double P1 = get_prob(1);
    double P2 = get_prob(2);
    
    // Heston Call Price: S * P1 - K * exp(-rT) * P2
    double call_price = S * P1 - K * exp(-r * T) * P2;
    
    if (is_call) {
        res.price = max(0.0, call_price);
    } else {
        // Put-Call Parity: P = C - S + K*exp(-r*T)
        // P = (S*P1 - K*exp(-rT)*P2) - S + K*exp(-rT)
        // P = S(P1 - 1) + K*exp(-rT)(1 - P2)
        res.price = max(0.0, call_price - S + K * exp(-r * T));
    }
    
    // Debug output if needed (comment out for prod)
    // std::cout << "P1: " << P1 << " P2: " << P2 << " Call: " << call_price << " Put: " << res.price << std::endl;

    return res;
}
