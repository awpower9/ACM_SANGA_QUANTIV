// binomial_engine.cpp
// High-performance Binomial Tree Options Pricing Engine
#include <cmath>
#include <algorithm>
#include <vector>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class BinomialEngine {
public:
    struct OptionResult {
        double price;
        double delta;
        double gamma;
        double theta;
        double vega;
        double rho;
    };

    // American option pricing using binomial tree
    double binomial_price(double S, double K, double T, double r, 
                         double sigma, bool is_call, int steps, 
                         bool american = true) const {
        if (T <= 0 || steps <= 0) {
            return is_call ? std::max(S - K, 0.0) : std::max(K - S, 0.0);
        }

        const double dt = T / steps;
        const double u = std::exp(sigma * std::sqrt(dt));
        const double d = 1.0 / u;
        const double p = (std::exp(r * dt) - d) / (u - d);
        const double discount = std::exp(-r * dt);

        // Initialize option values at maturity
        std::vector<double> option_values(steps + 1);
        
        // Calculate terminal stock prices and option values
        for (int i = 0; i <= steps; ++i) {
            double ST = S * std::pow(u, steps - i) * std::pow(d, i);
            option_values[i] = is_call ? std::max(ST - K, 0.0) : std::max(K - ST, 0.0);
        }

        // Backward induction through the tree
        for (int j = steps - 1; j >= 0; --j) {
            for (int i = 0; i <= j; ++i) {
                // Expected value (risk-neutral valuation)
                option_values[i] = discount * (p * option_values[i] + (1 - p) * option_values[i + 1]);
                
                // Check for early exercise (American option)
                if (american) {
                    double stock_price = S * std::pow(u, j - i) * std::pow(d, i);
                    double exercise_value = is_call ? 
                        std::max(stock_price - K, 0.0) : 
                        std::max(K - stock_price, 0.0);
                    option_values[i] = std::max(option_values[i], exercise_value);
                }
            }
        }

        return option_values[0];
    }

    // Calculate option price with all Greeks
    OptionResult calculate_option(double S, double K, double T, double r, 
                                  double sigma, bool is_call, int steps,
                                  bool american = true) const {
        OptionResult result;
        
        // Base price
        result.price = binomial_price(S, K, T, r, sigma, is_call, steps, american);

        // Calculate Greeks using finite differences
        const double dS = S * 0.01;  // 1% change in spot
        const double dT = 1.0 / 365.0;  // 1 day change
        const double dSigma = 0.01;  // 1% change in volatility
        const double dr = 0.01;  // 1% change in rate

        // Delta: ∂V/∂S
        double price_up = binomial_price(S + dS, K, T, r, sigma, is_call, steps, american);
        double price_down = binomial_price(S - dS, K, T, r, sigma, is_call, steps, american);
        result.delta = (price_up - price_down) / (2.0 * dS);

        // Gamma: ∂²V/∂S²
        result.gamma = (price_up - 2.0 * result.price + price_down) / (dS * dS);

        // Theta: ∂V/∂t (per day)
        if (T > dT) {
            double price_time_dec = binomial_price(S, K, T - dT, r, sigma, is_call, steps, american);
            result.theta = price_time_dec - result.price;
        } else {
            result.theta = -result.price / (T * 365.0);
        }

        // Vega: ∂V/∂σ (per 1% change)
        double price_vol_up = binomial_price(S, K, T, r, sigma + dSigma, is_call, steps, american);
        result.vega = (price_vol_up - result.price) / (dSigma * 100.0);

        // Rho: ∂V/∂r (per 1% change)
        double price_rate_up = binomial_price(S, K, T, r + dr, sigma, is_call, steps, american);
        result.rho = (price_rate_up - result.price) / (dr * 100.0);

        return result;
    }

    // Calculate option prices for a range of spot prices (for payoff diagrams)
    std::vector<double> calculate_payoff_range(double K, double T, double r, 
                                                double sigma, bool is_call,
                                                double min_price, double max_price, 
                                                int num_points, int steps,
                                                bool american = true) const {
        std::vector<double> prices;
        prices.reserve(num_points);
        double step_size = (max_price - min_price) / (num_points - 1);
        
        for (int i = 0; i < num_points; ++i) {
            double S = min_price + i * step_size;
            double price = binomial_price(S, K, T, r, sigma, is_call, steps, american);
            prices.push_back(price);
        }
        
        return prices;
    }

    // Calculate volatility surface
    std::vector<std::vector<double>> calculate_vol_surface(
            double S, double r, bool is_call, int steps,
            const std::vector<double>& strikes,
            const std::vector<double>& maturities,
            const std::vector<double>& vols,
            bool american = true) const {
        
        std::vector<std::vector<double>> surface;
        
        for (size_t i = 0; i < maturities.size(); ++i) {
            std::vector<double> row;
            for (size_t j = 0; j < strikes.size(); ++j) {
                size_t idx = i * strikes.size() + j;
                double sigma = (idx < vols.size()) ? vols[idx] : 0.20;
                double price = binomial_price(S, strikes[j], maturities[i], 
                                             r, sigma, is_call, steps, american);
                row.push_back(price);
            }
            surface.push_back(row);
        }
        
        return surface;
    }

    // Get the full binomial tree (for visualization)
    struct TreeNode {
        int step;
        int index;
        double stock_price;
        double option_value;
    };

    std::vector<TreeNode> get_tree_structure(double S, double K, double T, double r,
                                            double sigma, bool is_call, int steps,
                                            bool american = true) const {
        std::vector<TreeNode> tree;
        
        if (steps > 100) {
            // For large trees, only return subset for visualization
            steps = std::min(steps, 10);
        }

        const double dt = T / steps;
        const double u = std::exp(sigma * std::sqrt(dt));
        const double d = 1.0 / u;
        const double p = (std::exp(r * dt) - d) / (u - d);
        const double discount = std::exp(-r * dt);

        // Calculate all stock prices in the tree
        std::vector<std::vector<double>> stock_prices(steps + 1);
        std::vector<std::vector<double>> option_values(steps + 1);

        // Forward pass: calculate stock prices
        for (int j = 0; j <= steps; ++j) {
            stock_prices[j].resize(j + 1);
            option_values[j].resize(j + 1);
            
            for (int i = 0; i <= j; ++i) {
                stock_prices[j][i] = S * std::pow(u, j - i) * std::pow(d, i);
            }
        }

        // Terminal option values
        for (int i = 0; i <= steps; ++i) {
            option_values[steps][i] = is_call ? 
                std::max(stock_prices[steps][i] - K, 0.0) : 
                std::max(K - stock_prices[steps][i], 0.0);
        }

        // Backward induction
        for (int j = steps - 1; j >= 0; --j) {
            for (int i = 0; i <= j; ++i) {
                option_values[j][i] = discount * (p * option_values[j + 1][i] + 
                                                  (1 - p) * option_values[j + 1][i + 1]);
                
                if (american) {
                    double exercise_value = is_call ? 
                        std::max(stock_prices[j][i] - K, 0.0) : 
                        std::max(K - stock_prices[j][i], 0.0);
                    option_values[j][i] = std::max(option_values[j][i], exercise_value);
                }
            }
        }

        // Build tree nodes
        for (int j = 0; j <= steps; ++j) {
            for (int i = 0; i <= j; ++i) {
                TreeNode node;
                node.step = j;
                node.index = i;
                node.stock_price = stock_prices[j][i];
                node.option_value = option_values[j][i];
                tree.push_back(node);
            }
        }

        return tree;
    }
};

// Python bindings
PYBIND11_MODULE(binomial_engine, m) {
    m.doc() = "High-performance binomial tree options pricing engine";
    
    py::class_<BinomialEngine::OptionResult>(m, "OptionResult")
        .def_readonly("price", &BinomialEngine::OptionResult::price)
        .def_readonly("delta", &BinomialEngine::OptionResult::delta)
        .def_readonly("gamma", &BinomialEngine::OptionResult::gamma)
        .def_readonly("theta", &BinomialEngine::OptionResult::theta)
        .def_readonly("vega", &BinomialEngine::OptionResult::vega)
        .def_readonly("rho", &BinomialEngine::OptionResult::rho);
    
    py::class_<BinomialEngine::TreeNode>(m, "TreeNode")
        .def_readonly("step", &BinomialEngine::TreeNode::step)
        .def_readonly("index", &BinomialEngine::TreeNode::index)
        .def_readonly("stock_price", &BinomialEngine::TreeNode::stock_price)
        .def_readonly("option_value", &BinomialEngine::TreeNode::option_value);
    
    py::class_<BinomialEngine>(m, "BinomialEngine")
        .def(py::init<>())
        .def("binomial_price", &BinomialEngine::binomial_price,
             py::arg("S"), py::arg("K"), py::arg("T"), py::arg("r"),
             py::arg("sigma"), py::arg("is_call"), py::arg("steps"),
             py::arg("american") = true,
             "Calculate binomial tree option price")
        .def("calculate_option", &BinomialEngine::calculate_option,
             py::arg("S"), py::arg("K"), py::arg("T"), py::arg("r"),
             py::arg("sigma"), py::arg("is_call"), py::arg("steps"),
             py::arg("american") = true,
             "Calculate option price and Greeks")
        .def("calculate_payoff_range", &BinomialEngine::calculate_payoff_range,
             py::arg("K"), py::arg("T"), py::arg("r"), py::arg("sigma"),
             py::arg("is_call"), py::arg("min_price"), py::arg("max_price"),
             py::arg("num_points"), py::arg("steps"),
             py::arg("american") = true,
             "Calculate option prices over a range of spot prices")
        .def("calculate_vol_surface", &BinomialEngine::calculate_vol_surface,
             py::arg("S"), py::arg("r"), py::arg("is_call"), py::arg("steps"),
             py::arg("strikes"), py::arg("maturities"), py::arg("vols"),
             py::arg("american") = true,
             "Calculate option prices for volatility surface")
        .def("get_tree_structure", &BinomialEngine::get_tree_structure,
             py::arg("S"), py::arg("K"), py::arg("T"), py::arg("r"),
             py::arg("sigma"), py::arg("is_call"), py::arg("steps"),
             py::arg("american") = true,
             "Get complete tree structure for visualization");
}