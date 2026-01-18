#pragma once
#include <vector>
#include <cmath>
#include <algorithm>

struct OptionResult {
    double price;
    double delta;
    double gamma;
    double theta;
    double vega;
    double rho;
};

struct TreeNode {
    int step;
    int index;
    double stock_price;
    double option_value;
};

class BinomialEngine {
public:
    BinomialEngine() = default;

    OptionResult calculate_option(double S, double K, double T, double r, double v, bool is_call, int steps, bool american);

    std::vector<TreeNode> get_tree_structure(double S, double K, double T, double r, double v, bool is_call, int steps, bool american);

private:
    double calculate_single_price(double S, double K, double T, double r, double v, bool is_call, int steps, bool american);
};