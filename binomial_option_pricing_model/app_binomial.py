"""
Abstract Quantiv - Binomial Tree Options Pricing Dashboard
Professional-grade tool for visualizing binomial tree option pricing
"""

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Import the C++ binomial engine
# Note: In production, this would be: import binomial_engine
# For demonstration, we'll use a Python fallback
import sys
print(f"DEBUG: app_binomial.py starting on Python {sys.version}")

try:
    import binomial_engine
    engine = binomial_engine.BinomialEngine()
    USE_CPP = True
    print("✓ Using C++ binomial engine")
except ImportError as e:
    USE_CPP = False
    print(f"⚠ C++ engine not available, using Python fallback. Error: {e}")
    print(f"DEBUG: sys.path: {sys.path}")

# Python fallback implementation
class PythonBinomialEngine:
    def binomial_price(self, S, K, T, r, sigma, is_call, steps, american=True):
        if T <= 0 or steps <= 0:
            return max(S - K, 0) if is_call else max(K - S, 0)
        
        dt = T / steps
        u = np.exp(sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp(r * dt) - d) / (u - d)
        discount = np.exp(-r * dt)
        
        # Initialize option values at maturity
        option_values = np.zeros(steps + 1)
        
        # Calculate terminal stock prices and option values
        for i in range(steps + 1):
            ST = S * (u ** (steps - i)) * (d ** i)
            option_values[i] = max(ST - K, 0) if is_call else max(K - ST, 0)
        
        # Backward induction
        for j in range(steps - 1, -1, -1):
            for i in range(j + 1):
                option_values[i] = discount * (p * option_values[i] + (1 - p) * option_values[i + 1])
                
                if american:
                    stock_price = S * (u ** (j - i)) * (d ** i)
                    exercise_value = max(stock_price - K, 0) if is_call else max(K - stock_price, 0)
                    option_values[i] = max(option_values[i], exercise_value)
        
        return option_values[0]
    
    def calculate_option(self, S, K, T, r, sigma, is_call, steps, american=True):
        price = self.binomial_price(S, K, T, r, sigma, is_call, steps, american)
        
        # Calculate Greeks using finite differences
        dS = S * 0.01
        dT = 1 / 365
        dSigma = 0.01
        dr = 0.01
        
        price_up = self.binomial_price(S + dS, K, T, r, sigma, is_call, steps, american)
        price_down = self.binomial_price(S - dS, K, T, r, sigma, is_call, steps, american)
        delta = (price_up - price_down) / (2 * dS)
        
        gamma = (price_up - 2 * price + price_down) / (dS * dS)
        
        if T > dT:
            price_time_dec = self.binomial_price(S, K, T - dT, r, sigma, is_call, steps, american)
            theta = price_time_dec - price
        else:
            theta = -price / (T * 365)
        
        price_vol_up = self.binomial_price(S, K, T, r, sigma + dSigma, is_call, steps, american)
        vega = (price_vol_up - price) / (dSigma * 100)
        
        price_rate_up = self.binomial_price(S, K, T, r + dr, sigma, is_call, steps, american)
        rho = (price_rate_up - price) / (dr * 100)
        
        return type('obj', (object,), {
            'price': price, 'delta': delta, 'gamma': gamma,
            'theta': theta, 'vega': vega, 'rho': rho
        })()

if not USE_CPP:
    engine = PythonBinomialEngine()

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Abstract Quantiv - Binomial Tree"

# Color scheme
COLORS = {
    'background': '#0a0e27',
    'surface': '#141b3d',
    'primary': '#00d4ff',
    'secondary': '#7b61ff',
    'success': '#00ff88',
    'danger': '#ff4757',
    'text': '#e4e8ff',
    'text_secondary': '#8892b0'
}

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Abstract Quantiv", style={
            'margin': 0,
            'fontSize': '2rem',
            'fontWeight': '700',
            'color': 'white'
        }),
        html.P("Binomial Tree Options Pricing Model • American & European Options", style={
            'margin': '0.5rem 0 0 0',
            'fontSize': '0.95rem',
            'color': 'rgba(255, 255, 255, 0.8)'
        })
    ], style={
        'background': f'linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]})',
        'padding': '2rem',
        'boxShadow': '0 4px 20px rgba(0, 212, 255, 0.2)'
    }),
    
    # Main content
    html.Div([
        # Control Panel
        html.Div([
            html.H3("Model Parameters", style={'marginTop': 0, 'color': COLORS['primary']}),
            
            # Ticker input
            html.Div([
                html.Label("Stock Ticker", style={'color': COLORS['text_secondary'], 'fontSize': '0.875rem', 'fontWeight': 600}),
                dcc.Input(
                    id='ticker-input',
                    type='text',
                    value='AAPL',
                    placeholder='Enter ticker',
                    style={
                        'width': '100%',
                        'padding': '0.5rem',
                        'background': COLORS['background'],
                        'border': f'1px solid {COLORS["primary"]}',
                        'color': COLORS['text'],
                        'borderRadius': '4px',
                        'marginTop': '0.5rem'
                    }
                ),
                html.Button(
                    'Fetch Live Data',
                    id='fetch-button',
                    n_clicks=0,
                    style={
                        'marginTop': '0.5rem',
                        'padding': '0.5rem 1rem',
                        'background': f'linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]})',
                        'border': 'none',
                        'color': 'white',
                        'borderRadius': '4px',
                        'cursor': 'pointer',
                        'fontWeight': '600',
                        'width': '100%'
                    }
                )
            ], style={'marginBottom': '1.5rem'}),
            
            # Option type
            html.Div([
                html.Label("Option Type", style={'color': COLORS['text_secondary'], 'fontSize': '0.875rem', 'fontWeight': 600}),
                dcc.RadioItems(
                    id='option-type',
                    options=[
                        {'label': ' Call', 'value': 'call'},
                        {'label': ' Put', 'value': 'put'}
                    ],
                    value='call',
                    style={'color': COLORS['text'], 'marginTop': '0.5rem'},
                    labelStyle={'display': 'inline-block', 'marginRight': '1rem'}
                )
            ], style={'marginBottom': '1.5rem'}),
            
            # American vs European
            html.Div([
                html.Label("Exercise Style", style={'color': COLORS['text_secondary'], 'fontSize': '0.875rem', 'fontWeight': 600}),
                dcc.RadioItems(
                    id='exercise-style',
                    options=[
                        {'label': ' American', 'value': True},
                        {'label': ' European', 'value': False}
                    ],
                    value=True,
                    style={'color': COLORS['text'], 'marginTop': '0.5rem'},
                    labelStyle={'display': 'inline-block', 'marginRight': '1rem'}
                )
            ], style={'marginBottom': '1.5rem'}),
            
            # Number of steps
            html.Div([
                html.Label("Binomial Steps", style={'color': COLORS['text_secondary'], 'fontSize': '0.875rem', 'fontWeight': 600}),
                dcc.Slider(
                    id='num-steps',
                    min=10,
                    max=500,
                    step=10,
                    value=100,
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'
                ),
                html.Div("More steps = Higher accuracy", style={
                    'fontSize': '0.7rem',
                    'color': COLORS['text_secondary'],
                    'marginTop': '0.25rem'
                })
            ], style={'marginBottom': '1.5rem'}),
            
            # Spot price
            html.Div([
                html.Label("Spot Price ($)", style={'color': COLORS['text_secondary'], 'fontSize': '0.875rem', 'fontWeight': 600}),
                dcc.Slider(
                    id='spot-price',
                    min=50,
                    max=300,
                    step=1,
                    value=150,
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'
                )
            ], style={'marginBottom': '1.5rem'}),
            
            # Strike price
            html.Div([
                html.Label("Strike Price ($)", style={'color': COLORS['text_secondary'], 'fontSize': '0.875rem', 'fontWeight': 600}),
                dcc.Slider(
                    id='strike-price',
                    min=50,
                    max=300,
                    step=1,
                    value=150,
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'
                )
            ], style={'marginBottom': '1.5rem'}),
            
            # Time to expiration
            html.Div([
                html.Label("Time to Expiration (Years)", style={'color': COLORS['text_secondary'], 'fontSize': '0.875rem', 'fontWeight': 600}),
                dcc.Slider(
                    id='time-to-exp',
                    min=0.01,
                    max=2,
                    step=0.01,
                    value=0.5,
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'
                )
            ], style={'marginBottom': '1.5rem'}),
            
            # Volatility
            html.Div([
                html.Label("Volatility (σ)", style={'color': COLORS['text_secondary'], 'fontSize': '0.875rem', 'fontWeight': 600}),
                dcc.Slider(
                    id='volatility',
                    min=0.05,
                    max=1.0,
                    step=0.01,
                    value=0.25,
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'
                )
            ], style={'marginBottom': '1.5rem'}),
            
            # Risk-free rate
            html.Div([
                html.Label("Risk-Free Rate (%)", style={'color': COLORS['text_secondary'], 'fontSize': '0.875rem', 'fontWeight': 600}),
                dcc.Slider(
                    id='risk-free-rate',
                    min=0,
                    max=10,
                    step=0.1,
                    value=4.5,
                    marks=None,
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode='drag'
                )
            ], style={'marginBottom': '1.5rem'}),
            
            # Model info
            html.Div([
                html.Div("MODEL: BINOMIAL TREE", style={
                    'fontSize': '0.75rem',
                    'color': COLORS['text_secondary'],
                    'marginBottom': '0.5rem',
                    'fontWeight': 600
                }),
                html.Div(id='model-info', style={
                    'fontSize': '0.85rem',
                    'color': COLORS['text'],
                    'lineHeight': '1.5'
                })
            ], style={
                'background': COLORS['background'],
                'borderRadius': '8px',
                'padding': '1rem',
                'borderLeft': f'4px solid {COLORS["secondary"]}'
            })
            
        ], style={
            'background': COLORS['surface'],
            'borderRadius': '12px',
            'padding': '1.5rem',
            'width': '25%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'margin': '1rem'
        }),
        
        # Visualization area
        html.Div([
            # Metrics cards
            html.Div([
                html.Div([
                    html.H4("Option Price", style={'margin': '0 0 0.5rem 0', 'fontSize': '0.875rem', 'color': COLORS['text_secondary']}),
                    html.H2(id='option-price', style={'margin': 0, 'color': COLORS['success']})
                ], style={
                    'background': COLORS['surface'],
                    'borderRadius': '8px',
                    'padding': '1rem',
                    'borderLeft': f'4px solid {COLORS["success"]}',
                    'width': '15%',
                    'display': 'inline-block',
                    'margin': '0.5rem'
                }),
                
                html.Div([
                    html.H4("Delta (Δ)", style={'margin': '0 0 0.5rem 0', 'fontSize': '0.875rem', 'color': COLORS['text_secondary']}),
                    html.H2(id='delta', style={'margin': 0, 'color': COLORS['primary']})
                ], style={
                    'background': COLORS['surface'],
                    'borderRadius': '8px',
                    'padding': '1rem',
                    'borderLeft': f'4px solid {COLORS["primary"]}',
                    'width': '15%',
                    'display': 'inline-block',
                    'margin': '0.5rem'
                }),
                
                html.Div([
                    html.H4("Gamma (Γ)", style={'margin': '0 0 0.5rem 0', 'fontSize': '0.875rem', 'color': COLORS['text_secondary']}),
                    html.H2(id='gamma', style={'margin': 0, 'color': COLORS['primary']})
                ], style={
                    'background': COLORS['surface'],
                    'borderRadius': '8px',
                    'padding': '1rem',
                    'borderLeft': f'4px solid {COLORS["primary"]}',
                    'width': '15%',
                    'display': 'inline-block',
                    'margin': '0.5rem'
                }),
                
                html.Div([
                    html.H4("Theta (Θ)", style={'margin': '0 0 0.5rem 0', 'fontSize': '0.875rem', 'color': COLORS['text_secondary']}),
                    html.H2(id='theta', style={'margin': 0, 'color': COLORS['danger']})
                ], style={
                    'background': COLORS['surface'],
                    'borderRadius': '8px',
                    'padding': '1rem',
                    'borderLeft': f'4px solid {COLORS["danger"]}',
                    'width': '15%',
                    'display': 'inline-block',
                    'margin': '0.5rem'
                }),
                
                html.Div([
                    html.H4("Vega (ν)", style={'margin': '0 0 0.5rem 0', 'fontSize': '0.875rem', 'color': COLORS['text_secondary']}),
                    html.H2(id='vega', style={'margin': 0, 'color': COLORS['primary']})
                ], style={
                    'background': COLORS['surface'],
                    'borderRadius': '8px',
                    'padding': '1rem',
                    'borderLeft': f'4px solid {COLORS["primary"]}',
                    'width': '15%',
                    'display': 'inline-block',
                    'margin': '0.5rem'
                }),
                
                html.Div([
                    html.H4("Rho (ρ)", style={'margin': '0 0 0.5rem 0', 'fontSize': '0.875rem', 'color': COLORS['text_secondary']}),
                    html.H2(id='rho', style={'margin': 0, 'color': COLORS['primary']})
                ], style={
                    'background': COLORS['surface'],
                    'borderRadius': '8px',
                    'padding': '1rem',
                    'borderLeft': f'4px solid {COLORS["primary"]}',
                    'width': '15%',
                    'display': 'inline-block',
                    'margin': '0.5rem'
                }),
            ], style={'marginBottom': '1rem'}),
            
            # Charts
            html.Div([
                dcc.Graph(id='payoff-diagram', style={'height': '400px'})
            ], style={
                'background': COLORS['surface'],
                'borderRadius': '12px',
                'padding': '1.5rem',
                'marginBottom': '1rem'
            }),
            
            html.Div([
                html.Div([
                    dcc.Graph(id='greeks-chart', style={'height': '400px'})
                ], style={'width': '48%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(id='vol-surface', style={'height': '400px'})
                ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'})
            ], style={
                'background': COLORS['surface'],
                'borderRadius': '12px',
                'padding': '1.5rem'
            }),
            
        ], style={'width': '73%', 'display': 'inline-block', 'marginLeft': '0%', 'verticalAlign': 'top'}),
        
    ], style={'padding': '0'}),
    
    # Footer
    html.Div([
        html.P("Built with Binomial Tree Model (Cox-Ross-Rubinstein) • Supports American Options", style={'margin': 0}),
        html.P("🌲 High-performance C++ backend • Real-time pricing & Greeks", style={'marginTop': '0.5rem'})
    ], style={
        'textAlign': 'center',
        'padding': '2rem',
        'color': COLORS['text_secondary'],
        'fontSize': '0.875rem',
        'background': COLORS['background']
    }),
    
    # Hidden div to store fetched data
    dcc.Store(id='market-data')
    
], style={'background': COLORS['background'], 'minHeight': '100vh'})

# Callback to fetch live market data
@app.callback(
    [Output('spot-price', 'value'),
     Output('volatility', 'value'),
     Output('market-data', 'data')],
    [Input('fetch-button', 'n_clicks')],
    [State('ticker-input', 'value')]
)
def fetch_market_data(n_clicks, ticker):
    if n_clicks == 0:
        return dash.no_update, dash.no_update, None
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return dash.no_update, dash.no_update, None
        
        current_price = hist['Close'].iloc[-1]
        returns = np.log(hist['Close'] / hist['Close'].shift(1)).dropna()
        volatility = returns.std() * np.sqrt(252)
        
        return round(current_price, 2), round(volatility, 2), {
            'ticker': ticker,
            'price': current_price,
            'volatility': volatility
        }
    except:
        return dash.no_update, dash.no_update, None

# Main callback
@app.callback(
    [Output('option-price', 'children'),
     Output('delta', 'children'),
     Output('gamma', 'children'),
     Output('theta', 'children'),
     Output('vega', 'children'),
     Output('rho', 'children'),
     Output('model-info', 'children'),
     Output('payoff-diagram', 'figure'),
     Output('greeks-chart', 'figure'),
     Output('vol-surface', 'figure')],
    [Input('option-type', 'value'),
     Input('exercise-style', 'value'),
     Input('spot-price', 'value'),
     Input('strike-price', 'value'),
     Input('time-to-exp', 'value'),
     Input('volatility', 'value'),
     Input('risk-free-rate', 'value'),
     Input('num-steps', 'value')]
)
def update_dashboard(option_type, american, S, K, T, sigma, r_percent, steps):
    print(f"Callback triggered: S={S}, K={K}, T={T}, sigma={sigma}, r={r_percent}, steps={steps}")

    r = r_percent / 100
    is_call = (option_type == 'call')
    
    # Calculate option and Greeks
    result = engine.calculate_option(S, K, T, r, sigma, is_call, steps, american)
    
    # Format display
    price_text = f"${result.price:.2f}"
    delta_text = f"{result.delta:.4f}"
    gamma_text = f"{result.gamma:.4f}"
    theta_text = f"{result.theta:.4f}"
    vega_text = f"{result.vega:.4f}"
    rho_text = f"{result.rho:.4f}"
    
    model_info_text = f"Cox-Ross-Rubinstein (CRR) model with {steps} time steps. "
    model_info_text += f"{'American' if american else 'European'}-style {'call' if is_call else 'put'} option. "
    if american:
        model_info_text += "Early exercise optimization enabled."
    
    # Payoff diagram
    spot_range = np.linspace(S * 0.5, S * 1.5, 50)
    option_values = []
    intrinsic_values = []
    
    for spot in spot_range:
        price = engine.binomial_price(spot, K, T, r, sigma, is_call, steps, american)
        option_values.append(price)
        intrinsic = max(spot - K, 0) if is_call else max(K - spot, 0)
        intrinsic_values.append(intrinsic)
    
    payoff_fig = go.Figure()
    payoff_fig.add_trace(go.Scatter(
        x=spot_range, y=option_values,
        name='Option Value',
        line=dict(color=COLORS['primary'], width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 212, 255, 0.2)'
    ))
    payoff_fig.add_trace(go.Scatter(
        x=spot_range, y=intrinsic_values,
        name='Intrinsic Value',
        line=dict(color=COLORS['secondary'], width=2, dash='dash')
    ))
    payoff_fig.add_vline(x=S, line_dash="dot", line_color=COLORS['success'], 
                         annotation_text="Current Spot")
    payoff_fig.add_vline(x=K, line_dash="dot", line_color=COLORS['danger'], 
                         annotation_text="Strike")
    
    payoff_fig.update_layout(
        title="Payoff Diagram",
        xaxis_title="Spot Price ($)",
        yaxis_title="Option Value ($)",
        paper_bgcolor=COLORS['surface'],
        plot_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
        showlegend=True,
        legend=dict(bgcolor=COLORS['surface']),
        hovermode='x unified'
    )
    
    # Greeks chart
    spot_range_greeks = np.linspace(S * 0.7, S * 1.3, 30)
    deltas, gammas, vegas = [], [], []
    
    for spot in spot_range_greeks:
        res = engine.calculate_option(spot, K, T, r, sigma, is_call, steps, american)
        deltas.append(res.delta)
        gammas.append(res.gamma * 10)
        vegas.append(res.vega)
    
    greeks_fig = go.Figure()
    greeks_fig.add_trace(go.Scatter(x=spot_range_greeks, y=deltas, name='Delta', 
                                    line=dict(color=COLORS['primary'], width=3)))
    greeks_fig.add_trace(go.Scatter(x=spot_range_greeks, y=gammas, name='Gamma (×10)', 
                                    line=dict(color=COLORS['secondary'], width=3)))
    greeks_fig.add_trace(go.Scatter(x=spot_range_greeks, y=vegas, name='Vega', 
                                    line=dict(color=COLORS['success'], width=3)))
    
    greeks_fig.update_layout(
        title="Greeks Sensitivity",
        xaxis_title="Spot Price ($)",
        yaxis_title="Greek Value",
        paper_bgcolor=COLORS['surface'],
        plot_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
        showlegend=True,
        legend=dict(bgcolor=COLORS['surface']),
        hovermode='x unified'
    )
    
    # Volatility surface
    strikes = np.linspace(K * 0.8, K * 1.2, 15)
    maturities = np.linspace(0.1, 1.5, 15)
    surface = np.zeros((len(maturities), len(strikes)))
    
    for i, mat in enumerate(maturities):
        for j, strike in enumerate(strikes):
            surface[i, j] = engine.binomial_price(S, strike, mat, r, sigma, is_call, steps, american)
    
    vol_fig = go.Figure(data=[go.Surface(
        x=strikes,
        y=maturities,
        z=surface,
        colorscale='Viridis',
        colorbar=dict(title="Price")
    )])
    
    vol_fig.update_layout(
        title="Option Price Surface",
        scene=dict(
            xaxis_title="Strike Price",
            yaxis_title="Time to Maturity",
            zaxis_title="Option Price",
            bgcolor=COLORS['background']
        ),
        paper_bgcolor=COLORS['surface'],
        font=dict(color=COLORS['text']),
        height=400
    )
    
    return (price_text, delta_text, gamma_text, theta_text, vega_text, rho_text,
            model_info_text, payoff_fig, greeks_fig, vol_fig)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  ABSTRACT QUANTIV - BINOMIAL TREE OPTIONS PRICING")
    print("="*60)
    print(f"\n  Engine: {'C++ (High Performance)' if USE_CPP else 'Python (Fallback)'}")
    print(f"  Model: Cox-Ross-Rubinstein Binomial Tree")
    print(f"  Features: American & European Options")
    print(f"\n  Starting server at http://localhost:8050")
    print("="*60 + "\n")
    
    app.run_server(debug=True, port=8050)