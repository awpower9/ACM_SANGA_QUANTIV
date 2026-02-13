#pragma once
#include <vector>
#include <cmath>
#include <algorithm>
#include "../include/black_scholes.h" // reuse BSMResult or define new one

// We can reuse OptionResult from binomial.h but since that header might not be included everywhere 
// let's define a similar struct or reuse OptionResult if we include binomial.h
// To follow clean dependency, lets include binomial.h for the result struct if possible, 
// OR simpler: just define it locally if we want decoupling. 
// Given the existing patterns, let's just use BSMResult format or similar. 
// Actually, `OptionResult` is in `binomial.h`. Let's include that.

#include "../include/binomial.h" 

class TrinomialEngine {
public:
    TrinomialEngine() = default;

    OptionResult calculate_option(double S, double K, double T, double r, double sigma, 
                                  bool is_call, int steps, bool american);

    std::vector<TreeNode> get_tree_structure(double S, double K, double T, double r, double sigma, 
                                             bool is_call, int steps, bool american);
};
