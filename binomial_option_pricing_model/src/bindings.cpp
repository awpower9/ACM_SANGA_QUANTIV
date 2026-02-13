#include <pybind11/pybind11.h>
#include <pybind11/stl.h>       
#include "../include/black_scholes.h"
#include "../include/binomial.h"
#include "../include/merton_model.h"
#include "../include/heston_model.h"

#include "../include/trinomial.h"

namespace py = pybind11;

PYBIND11_MODULE(quantiv_engine, m) {
    m.doc() = "Quantiv Engine";

    py::class_<OptionResult>(m, "OptionResult")
        .def_readonly("price", &OptionResult::price)
        .def_readonly("delta", &OptionResult::delta)
        .def_readonly("gamma", &OptionResult::gamma)
        .def_readonly("theta", &OptionResult::theta)
        .def_readonly("vega", &OptionResult::vega)
        .def_readonly("rho", &OptionResult::rho);

    py::class_<TreeNode>(m, "TreeNode")
        .def_readonly("step", &TreeNode::step)
        .def_readonly("index", &TreeNode::index)
        .def_readonly("stock_price", &TreeNode::stock_price)
        .def_readonly("option_value", &TreeNode::option_value);

    py::class_<BinomialEngine>(m, "BinomialEngine")
        .def(py::init<>())
        .def("calculate_option", &BinomialEngine::calculate_option)
        .def("get_tree_structure", &BinomialEngine::get_tree_structure);

    py::class_<TrinomialEngine>(m, "TrinomialEngine")
        .def(py::init<>())
        .def("calculate_option", &TrinomialEngine::calculate_option)
        .def("get_tree_structure", &TrinomialEngine::get_tree_structure);

    py::class_<BSMResult>(m, "BSMResult")
        .def_readonly("price", &BSMResult::price)
        .def_readonly("delta", &BSMResult::delta)
        .def_readonly("gamma", &BSMResult::gamma)
        .def_readonly("theta", &BSMResult::theta)
        .def_readonly("vega", &BSMResult::vega)
        .def_readonly("rho", &BSMResult::rho);

    py::class_<BlackScholes>(m, "BlackScholes")
        .def(py::init<>())
        .def("calculate", &BlackScholes::calculate);

    py::class_<MJDResult>(m, "MJDResult")
        .def_readonly("price", &MJDResult::price)
        .def_readonly("delta", &MJDResult::delta)
        .def_readonly("gamma", &MJDResult::gamma)
        .def_readonly("vega", &MJDResult::vega)
        .def_readonly("theta",&MJDResult::theta)
        .def_readonly("rho",&MJDResult::rho);

    py::class_<Merton>(m,"Merton")
        .def(py::init<>())
        .def("calculate",&Merton::calculate);

    py::class_<HestonResult>(m, "HestonResult")
        .def_readonly("price", &HestonResult::price)
        .def_readonly("delta", &HestonResult::delta)
        .def_readonly("gamma", &HestonResult::gamma)
        .def_readonly("theta", &HestonResult::theta)
        .def_readonly("vega", &HestonResult::vega)
        .def_readonly("rho", &HestonResult::rho);

    py::class_<Heston>(m, "Heston")
        .def(py::init<>())
        .def("calculate", &Heston::calculate);
}