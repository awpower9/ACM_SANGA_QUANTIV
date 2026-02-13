import dash
from dash import dcc,html
from dash.dependencies import Input,Output
import plotly.graph_objects as go

dash.register_page(__name__, path="/")

layout = html.Div([
    # Hero Section
    html.Div([
        html.H1("QuantIV", className="hero-title"),
        html.H2("Interactive Option Pricing & Risk Analytics", className="hero-subtitle"),
    ], className="hero-section"),

    # Educational Model List (Vertical Stack)
    html.Div([
        # --- Card 1: Binomial ---
        html.Details([
            html.Summary([
                html.H3("Binomial Model", className="accordion-title"),
                html.Span("Discrete-time lattice model for American options.", className="card-short-desc")
            ]),
            html.Div([
                html.H4("Concept"),
                dcc.Markdown("The Binomial Option Pricing Model (BOPM) provides a numerical method for the valuation of options. It constructs a recombining tree where the stock price moves up ($u$) or down ($d$) by a specific factor at each time step. The option value is calculated backwards from expiry to the present.", className="card-detail-text"),
                
                html.H4("Key Assumptions"),
                dcc.Markdown("""
                *   The stock price follows a multiplicative binomial process.
                *   No arbitrage opportunities exist.
                *   Risk-free rate remains constant.
                *   Markets are frictionless (no taxes or transaction costs).
                """, className="card-detail-text"),
                
                html.H4("Formula"),
                dcc.Markdown("$$V_n = e^{-r\\Delta t} [p V_{n+1}^u + (1-p) V_{n+1}^d]$$", mathjax=True, className="card-formula"),
                dcc.Markdown("Where $p = \\frac{e^{r\\Delta t} - d}{u - d}$ is the risk-neutral probability.", mathjax=True, className="card-detail-text"),

                html.H4("Best Use Case"),
                dcc.Markdown("Pricing **American Options** which can be exercised early. It handles discrete dividends and complex features better than Black-Scholes.", className="card-detail-text"),
                
                dcc.Link("Simulate Binomial Model", href="/models?model=binomial", className="learn-btn-full")
            ], className="card-details-content")
        ], className="model-card"),

        # --- Card 2: Trinomial ---
        html.Details([
            html.Summary([
                html.H3("Trinomial Model", className="accordion-title"),
                html.Span("Accelerated lattice model with 3 branches.", className="card-short-desc")
            ]),
            html.Div([
                html.H4("Concept"),
                dcc.Markdown("The Trinomial model is an extension of the binomial tree where the stock price can move **Up**, **Down**, or stay **Flat** (Stable) at each step. This extra degree of freedom allows the tree to align better with the time and space grid, resulting in faster convergence.", className="card-detail-text"),
                
                html.H4("Advantages"),
                dcc.Markdown("""
                *   **Converges faster** than the Binomial model (fewer steps for same accuracy).
                *   More numerically stable.
                *   Better for pricing Barrier Options and other path-dependent exotics.
                """, className="card-detail-text"),
                
                html.H4("Formula"),
                dcc.Markdown("$$V_n = e^{-r\\Delta t} [p_u V_{u} + p_m V_{m} + p_d V_{d}]$$", mathjax=True, className="card-formula"),
                
                html.H4("Best Use Case"),
                dcc.Markdown("When computation speed and accuracy are critical, or for pricing complex Exotics.", className="card-detail-text"),
                
                dcc.Link("Simulate Trinomial Model", href="/models?model=trinomial", className="learn-btn-full")
            ], className="card-details-content")
        ], className="model-card"),

        # --- Card 3: Black-Scholes ---
        html.Details([
            html.Summary([
                html.H3("Black-Scholes", className="accordion-title"),
                html.Span("Standard closed-form solution for European options.", className="card-short-desc")
            ]),
            html.Div([
                html.H4("Concept"),
                dcc.Markdown("Published in 1973 by Black, Scholes, and Merton, this model revolutionized finance. It provides a standard formula to calculate the theoretical price of European options, assuming the asset follows a Geometric Brownian Motion (GBM).", className="card-detail-text"),
                
                html.H4("Key Assumptions"),
                dcc.Markdown("""
                *   **Log-normal distribution** of stock prices.
                *   **Constant volatility** ($\sigma$) and risk-free rate ($r$).
                *   No dividends (in the original formulation).
                *   Option can only be exercised at expiration (European).
                """, className="card-detail-text"),
                
                html.H4("Formula"),
                dcc.Markdown("$$C = S N(d_1) - K e^{-rt} N(d_2)$$", mathjax=True, className="card-formula"),
                dcc.Markdown("$$d_1 = \\frac{\\ln(S/K) + (r + \\sigma^2/2)t}{\\sigma\\sqrt{t}}$$ and $$d_2 = d_1 - \\sigma\\sqrt{t}$$", mathjax=True, className="card-detail-text"),
                
                html.H4("Best Use Case"),
                dcc.Markdown("Quick valuation of **European Options** and calculating Greeks (Delta, Gamma, Vega, Theta, Rho).", className="card-detail-text"),
                
                dcc.Link("Simulate Black-Scholes", href="/models?model=BlackScholes", className="learn-btn-full")
            ], className="card-details-content")
        ], className="model-card"),

        # --- Card 4: Merton Jump ---
        html.Details([
            html.Summary([
                html.H3("Merton Jump", className="accordion-title"),
                html.Span("Captures sudden market shocks (crashes).", className="card-short-desc")
            ]),
            html.Div([
                html.H4("Concept"),
                dcc.Markdown("Standard models assume price changes are continuous. However, markets often experience sudden shocks (e.g., earnings, geopolitical events). Merton (1976) added a **Poisson Jump Process** to the BSM framework to model these discontinuities.", className="card-detail-text"),
                
                html.H4("Key Features"),
                dcc.Markdown("""
                *   **Jump Diffusion**: Composed of a continuous diffusion part and a discontinuous jump part.
                *   **Fat Tails**: Can generate return distributions with higher kurtosis (more extreme outcomes) than the normal distribution.
                """, className="card-detail-text"),
                
                html.H4("Dynamics"),
                dcc.Markdown("$$dS_t = (\\mu - \\lambda k) S_t dt + \\sigma S_t dW_t + (J-1) S_t dN_t$$", mathjax=True, className="card-formula"),
                
                html.H4("Best Use Case"),
                dcc.Markdown("Markets with high likelihood of **extreme events**, or when pricing deep out-of-the-money puts.", className="card-detail-text"),
                
                dcc.Link("Simulate Merton Jump", href="/advmodels?model=Merton", className="learn-btn-full")
            ], className="card-details-content")
        ], className="model-card"),

        # --- Card 5: Heston ---
        html.Details([
            html.Summary([
                html.H3("Heston Model", className="accordion-title"),
                html.Span("Stochastic volatility model for real-world skew.", className="card-short-desc")
            ]),
            html.Div([
                html.H4("Concept"),
                dcc.Markdown("The Black-Scholes assumption of constant volatility is often violated in reality (implied volatility smile). The Heston model (1993) addresses this by modeling volatility as a random process itself.", className="card-detail-text"),
                
                html.H4("Key Parameters"),
                dcc.Markdown("""
                *   $\\kappa$: Speed of mean reversion.
                *   $\\theta$: Long-run average variance.
                *   $\\xi$: Volatility of volatility (vol-of-vol).
                *   $\\rho$: Correlation between asset and volatility Brownian motions.
                """, className="card-detail-text", mathjax=True),
                
                html.H4("Dynamics"),
                dcc.Markdown("$$dv_t = \\kappa(\\theta - v_t)dt + \\xi \\sqrt{v_t} dW_t^v$$", mathjax=True, className="card-formula"),
                
                html.H4("Best Use Case"),
                dcc.Markdown("Pricing exotics, long-dated options, or when the **Volatility Smile/Skew** is significant.", className="card-detail-text"),
                
                dcc.Link("Simulate Heston Model", href="/advmodels?model=Heston", className="learn-btn-full")
            ], className="card-details-content")
        ], className="model-card"),
        
    ], className="model-grid")

], className="home_container")
