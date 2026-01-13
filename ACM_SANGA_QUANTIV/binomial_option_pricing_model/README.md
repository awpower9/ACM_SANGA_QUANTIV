# Abstract Quantiv - Binomial Tree Options Pricing

A professional-grade, interactive dashboard for visualizing and pricing options using the Cox-Ross-Rubinstein (CRR) Binomial Tree model. This project combines a high-performance C++ calculation engine with a modern Python/Dash user interface.

## 🚀 Features

-   **High-Performance Engine**: Core pricing algorithms implemented in C++ (via `pybind11`) for lightning-fast calculations even with high step counts.
-   **Interactive Dashboard**: Built with Dash and Plotly for real-time visualization.
-   **Visualizations**:
    -   **Dynamic Binomial Tree**: Visualize the stock price evolution and option value at each node.
    -   **Payoff Diagram**: Interactive chart showing profit/loss scenarios.
    -   **Greeks Analysis**: Real-time sensitivity analysis (Delta, Gamma, Theta, Vega, Rho).
    -   **Volatility Surface**: 3D visualization of option prices across strikes and maturities.
-   **Live Market Data**: Fetch real-time stock prices and volatility estimates using `yfinance` with a single click.
-   **Flexible Modeling**: Support for both **American** and **European** options.

## 🛠️ Prerequisites

-   **Python**: 3.8 or higher
-   **C++ Compiler**:
    -   **Windows**: Microsoft Visual Studio 2019/2022 (with "Desktop development with C++" workload)
    -   **Linux/macOS**: GCC or Clang
-   **Git**

## 📦 Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/ACM_SANGA_QUANTIV.git
    cd ACM_SANGA_QUANTIV/binomial_option_pricing_model
    ```

2.  **Create a Virtual Environment (Recommended)**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Linux/Mac
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Build the C++ Engine**
    This step compiles the C++ backend into a Python extension.
    ```bash
    python setup.py build_ext --inplace
    ```
    *Note: If you encounter errors, ensure your C++ compiler is correctly installed and added to your system PATH.*

## 🖥️ Usage

1.  **Run the Application**
    ```bash
    python app_binomial.py
    ```

2.  **Access the Dashboard**
    Open your web browser and navigate to:
    `http://localhost:8050`

3.  **Interact**
    -   **Fetch Market Data**: Enter a stock ticker (e.g., AAPL, NVDA) and click **"Fetch Live Data"**. The Spot Price ($S$) and Volatility ($\sigma$) sliders will automatically update to current market values.
    -   **Manual Control**: You can still manually adjust all sliders to test different scenarios.
    -   **Styles**: Switch between **American** and **European** exercise styles.
    -   **Visualize**: View the real-time updates on the Tree, Payoff Diagram, and Greeks.


## 📂 Project Structure

-   `app_binomial.py`: Main application entry point (Dash frontend).
-   `binomial_engine.cpp`: C++ source code for the pricing engine.
-   `market_data_service.py`: Python module handles fetching price and volatility from Yahoo Finance.
-   `setup.py`: Build script for the C++ extension.
-   `CMakeLists.txt`: CMake configuration (alternative build method).
-   `requirements.txt`: Python package dependencies.
-   `assets/`: Static assets (CSS/Images).

## 🔧 Troubleshooting

-   **"C++ engine not available, using Python fallback"**:
    This means the C++ extension hasn't been built or loaded correctly. Run `python setup.py build_ext --inplace` again and check for errors.
-   **App.run_server error**:
    Ensure you are using the latest version of Dash. If using an older version, you might need `app.run_server()` instead of `app.run()`.
