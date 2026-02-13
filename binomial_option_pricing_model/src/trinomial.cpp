#include "../include/trinomial.h"
#include <iostream>
#include <algorithm>

OptionResult TrinomialEngine::calculate_option(double S, double K, double T, double r, double sigma, 
                                               bool is_call, int steps, bool american) {
    // 6-field initializer for OptionResult
    OptionResult res = {0.0, 0.0, 0.0, 0.0, 0.0, 0.0};

    if (steps <= 0) return res;

    double dt = T / steps;
    
    // Standard Trinomial Parameters (u = exp(sigma * sqrt(3 * dt)))
    double dx = sigma * std::sqrt(3.0 * dt);
    double u = std::exp(dx);
    // d = 1/u (implied geometry)
    
    // Probabilities
    // drift = r - 0.5 * sigma^2
    double drift = r - 0.5 * sigma * sigma;
    
    // Standard approximations for probabilities
    // pu = 0.5 * ( (sigma^2 dt + (drift*dt)^2 ) / dx^2 + (drift*dt)/dx )
    double pu = 0.5 * ( (sigma*sigma*dt + drift*drift*dt*dt) / (dx*dx) + (drift*dt)/dx );
    double pd = 0.5 * ( (sigma*sigma*dt + drift*drift*dt*dt) / (dx*dx) - (drift*dt)/dx );
    double pm = 1.0 - pu - pd;
    
    double disc = std::exp(-r * dt);
    
    // Initialize price vector at maturity
    // Size is 2*N + 1 nodes centered at 0
    int num_nodes = 2 * steps + 1;
    std::vector<double> values(num_nodes);
    
    for (int i = 0; i < num_nodes; ++i) {
        // Node index relative to center: i - steps
        // i=0 -> -steps * dx
        // i=steps -> 0 
        // i=2*steps -> +steps * dx
        
        int offset = i - steps;
        double St = S * std::exp(offset * dx);
        values[i] = is_call ? std::max(0.0, St - K) : std::max(0.0, K - St);
    }
    
    // Backward Induction
    for (int j = steps - 1; j >= 0; --j) {
        // At step j, we need values for nodes 0 to 2*j
        // The array 'values' currently holds 2*(j+1) + 1 elements aka 2j+3
        // Node i at step j (where i goes 0 to 2j) connects to:
        // i (down), i+1 (mid), i+2 (up) in the previous array (which corresponds to step j+1)
        // Wait, let's verify indices.
        // Step 0 (root) has 1 node (i=0). Connects to 0,1,2 of Step 1? Yes.
        
        std::vector<double> next_values(2 * j + 1);
        for(int i = 0; i < 2 * j + 1; ++i) {
             double val = disc * (pd * values[i] + pm * values[i+1] + pu * values[i+2]);
             
             if (american) {
                 // Calculate intrinsic value at node (j, i)
                 // Offset calc: center of this layer is index j.
                 // So offset = i - j.
                 int offset = i - j; 
                 double St = S * std::exp(offset * dx);
                 double intrinsic = is_call ? std::max(0.0, St - K) : std::max(0.0, K - St);
                 val = std::max(val, intrinsic);
             }
             next_values[i] = val;
        }
        values = next_values; // Swap
    }

    res.price = values[0];
    return res;
}

std::vector<TreeNode> TrinomialEngine::get_tree_structure(double S, double K, double T, double r, double sigma, 
                                                          bool is_call, int steps, bool american) {
    std::vector<TreeNode> tree_nodes;
    if (steps <= 0) return tree_nodes;

    double dt = T / steps;
    double dx = sigma * std::sqrt(3.0 * dt);
    double u = std::exp(dx);
    double drift = r - 0.5 * sigma * sigma;
    
    double pu = 0.5 * ( (sigma*sigma*dt + drift*drift*dt*dt) / (dx*dx) + (drift*dt)/dx );
    double pd = 0.5 * ( (sigma*sigma*dt + drift*drift*dt*dt) / (dx*dx) - (drift*dt)/dx );
    double pm = 1.0 - pu - pd;
    double disc = std::exp(-r * dt);
    
    // 1. Forward Pass: Calculate Stock Prices and Store Nodes
    // We need to store nodes layer by layer to construct the tree logic later if needed,
    // but for simple visualization, a flat list of nodes properly marked with step/index is enough.
    
    // Actually, to get Option Values, we need the Backward Induction process.
    // So we will simulate the backward induction but keeping track of full state?
    // Memory efficient way:
    // 1. Calculate all S at final step.
    // 2. Backward induction to get Option Values at all steps.
    // 3. Store (Step, Index, S, OptionValue)
    
    // Let's use a vector of vectors for the backward pass
    // vector[step][index] = {S, Value}
    
    int num_layers = steps + 1;
    std::vector<std::vector<std::pair<double, double>>> grid(num_layers);
    
    // Fill Stock Prices (Forward)
    for (int j = 0; j <= steps; ++j) {
        int nodes_in_layer = 2 * j + 1;
        grid[j].resize(nodes_in_layer);
        for (int i = 0; i < nodes_in_layer; ++i) {
            int offset = i - j; 
            grid[j][i].first = S * std::exp(offset * dx);
        }
    }
    
    // Initialize Option Values at Maturity
    for (int i = 0; i < 2 * steps + 1; ++i) {
        double St = grid[steps][i].first;
        grid[steps][i].second = is_call ? std::max(0.0, St - K) : std::max(0.0, K - St);
    }
    
    // Backward Induction for Values
    for (int j = steps - 1; j >= 0; --j) {
        for (int i = 0; i < 2 * j + 1; ++i) {
             double val = disc * (pd * grid[j+1][i].second + pm * grid[j+1][i+1].second + pu * grid[j+1][i+2].second);
             if (american) {
                 double St = grid[j][i].first;
                 double intrinsic = is_call ? std::max(0.0, St - K) : std::max(0.0, K - St);
                 val = std::max(val, intrinsic);
             }
             grid[j][i].second = val;
        }
    }
    
    // Flatten to vector<TreeNode>
    for (int j = 0; j <= steps; ++j) {
        for (int i = 0; i < (int)grid[j].size(); ++i) {
             // Re-center index for visual clarity? 
             // Standard index 0..2j is fine.
             tree_nodes.push_back({j, i, grid[j][i].first, grid[j][i].second});
        }
    }
    
    return tree_nodes;
}
