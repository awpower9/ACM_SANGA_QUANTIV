#include "../include/binomial.h"
#include <iostream>

double BinomialEngine::calculate_single_price(double S, double K, double T, double r, double v, bool is_call, int steps, bool american) {
    if (steps <= 0 || T <= 0) return is_call ? std::max(S - K, 0.0) : std::max(K - S, 0.0);
    
    double dt = T / steps;
    double u = std::exp(v * std::sqrt(dt));
    double d = 1.0 / u;
    double p = (std::exp(r * dt) - d) / (u - d);
    double discount = std::exp(-r * dt);

    std::vector<double> values(steps + 1);

    for (int i = 0; i <= steps; ++i) {
        double ST = S * std::pow(u, steps - i) * std::pow(d, i);
        values[i] = is_call ? std::max(ST - K, 0.0) : std::max(K - ST, 0.0);
    }

    for (int j = steps - 1; j >= 0; --j) {
        for (int i = 0; i <= j; ++i) {
            double val = discount * (p * values[i] + (1.0 - p) * values[i + 1]);
            if (american) {
                double ST = S * std::pow(u, j - i) * std::pow(d, i);
                double exercise = is_call ? std::max(ST - K, 0.0) : std::max(K - ST, 0.0);
                val = std::max(val, exercise);
            }
            values[i] = val;
        }
    }
    return values[0];
}

OptionResult BinomialEngine::calculate_option(double S, double K, double T, double r, double v, bool is_call, int steps, bool american) {
    OptionResult res;
    
    // Base Price
    res.price = calculate_single_price(S, K, T, r, v, is_call, steps, american);

    // Finite Difference settings
    double dS = S * 0.01;
    double dT = 1.0 / 365.0; 
    double dV = 0.01;        
    double dR = 0.01;        

    // Delta & Gamma
    double p_up = calculate_single_price(S + dS, K, T, r, v, is_call, steps, american);
    double p_down = calculate_single_price(S - dS, K, T, r, v, is_call, steps, american);
    res.delta = (p_up - p_down) / (2 * dS);
    res.gamma = (p_up - 2 * res.price + p_down) / (dS * dS);

    // Theta (Time Decay)
    if (T > dT) {
        double p_t = calculate_single_price(S, K, T - dT, r, v, is_call, steps, american);
        res.theta = (p_t - res.price); // Per day change
    } else {
        res.theta = 0.0;
    }

    // Vega (Volatility)
    double p_vol = calculate_single_price(S, K, T, r, v + dV, is_call, steps, american);
    res.vega = (p_vol - res.price) / (dV * 100.0); // Scaled for 1% change

    // Rho (Interest Rate)
    double p_rho = calculate_single_price(S, K, T, r + dR, v, is_call, steps, american);
    res.rho = (p_rho - res.price) / (dR * 100.0); // Scaled for 1% change

    return res;
}

// 2. Visualization Tree Structure
std::vector<TreeNode> BinomialEngine::get_tree_structure(double S, double K, double T, double r, double v, bool is_call, int steps, bool american) {
    std::vector<TreeNode> nodes;
    
    // Limit steps for visualization to prevent crashing browser
    int vis_steps = std::min(steps, 15); 
    
    double dt = T / vis_steps;
    double u = std::exp(v * std::sqrt(dt));
    double d = 1.0 / u;
    double p = (std::exp(r * dt) - d) / (u - d);
    double discount = std::exp(-r * dt);

    // We need to store full grid to trace back
    // Use a flat vector for 2D grid: grid[step][index]
    // But since size changes per step, a vector of vectors is easier here
    std::vector<std::vector<double>> prices(vis_steps + 1);
    std::vector<std::vector<double>> values(vis_steps + 1);

    // Forward pass: Stock Prices
    for (int j = 0; j <= vis_steps; ++j) {
        prices[j].resize(j + 1);
        values[j].resize(j + 1);
        for (int i = 0; i <= j; ++i) {
            prices[j][i] = S * std::pow(u, j - i) * std::pow(d, i);
        }
    }

    // Initialize Option Values at Maturity
    for (int i = 0; i <= vis_steps; ++i) {
        values[vis_steps][i] = is_call ? std::max(prices[vis_steps][i] - K, 0.0) : std::max(K - prices[vis_steps][i], 0.0);
    }

    // Backward Induction
    for (int j = vis_steps - 1; j >= 0; --j) {
        for (int i = 0; i <= j; ++i) {
            double val = discount * (p * values[j + 1][i] + (1.0 - p) * values[j + 1][i + 1]);
            if (american) {
                double exercise = is_call ? std::max(prices[j][i] - K, 0.0) : std::max(K - prices[j][i], 0.0);
                val = std::max(val, exercise);
            }
            values[j][i] = val;
        }
    }

    // Flatten into TreeNode vector
    for (int j = 0; j <= vis_steps; ++j) {
        for (int i = 0; i <= j; ++i) {
            nodes.push_back({j, i, prices[j][i], values[j][i]});
        }
    }

    return nodes;
}