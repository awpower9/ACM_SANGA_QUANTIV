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
try:
    import binomial_engine
    engine = binomial_engine.BinomialEngine()
    USE_CPP = True
    print("✓ Using C++ binomial engine")
except ImportError:
    USE_CPP = False
    print("⚠ C++ engine not available, using Python fallback")

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
    
    def get_tree_structure(self, S, K, T, r, sigma, is_call, steps, american=True):
        if steps > 15:
            steps = 15  # Limit for visualization
            
        dt = T / steps
        u = np.exp(sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp(r * dt) - d) / (u - d)
        discount = np.exp(-r * dt)
        
        # Calculate stock prices
        stock_prices = []
        for j in range(steps + 1):
            row = []
            for i in range(j + 1):
                price = S * (u ** (j - i)) * (d ** i)
                row.append(price)
            stock_prices.append(row)
            
        # Calculate option values
        option_values = [[0.0] * (j + 1) for j in range(steps + 1)]
        
        # Terminal values
        for i in range(steps + 1):
            val = max(stock_prices[steps][i] - K, 0) if is_call else max(K - stock_prices[steps][i], 0)
            option_values[steps][i] = val
            
        # Backward induction
        for j in range(steps - 1, -1, -1):
            for i in range(j + 1):
                val = discount * (p * option_values[j + 1][i] + (1 - p) * option_values[j + 1][i + 1])
                if american:
                    exercise = max(stock_prices[j][i] - K, 0) if is_call else max(K - stock_prices[j][i], 0)
                    val = max(val, exercise)
                option_values[j][i] = val
                
        # Flatten to list of nodes
        nodes = []
        for j in range(steps + 1):
            for i in range(j + 1):
                node = type('TreeNode', (object,), {
                    'step': j,
                    'index': i,
                    'stock_price': stock_prices[j][i],
                    'option_value': option_values[j][i]
                })()
                nodes.append(node)
                
        return nodes

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
# App layout
app.layout = html.Div([
    # Sidebar (Controls)
    html.Div([
        # Header
        html.Div([
            html.H1("Abstract Quantiv", style={
                'margin': 0,
                'fontSize': '1.5rem',
                'fontWeight': '700',
                'color': 'white'
            }),
            html.P("Binomial Pricing Model", style={
                'margin': '0.5rem 0 0 0',
                'fontSize': '0.85rem',
                'color': 'rgba(255, 255, 255, 0.8)'
            })
        ], style={
            'marginBottom': '2rem',
            'paddingBottom': '1rem',
            'borderBottom': f'1px solid {COLORS["surface"]}'
        }),

        # Control Panel Content
        html.H3("Parameters", style={'marginTop': 0, 'color': COLORS['primary'], 'fontSize': '1.1rem'}),
        
        # Ticker input
        html.Div([
            html.Label("Stock Ticker", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem', 'fontWeight': 600}),
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
                    'marginTop': '0.25rem'
                }
            ),
            html.Button(
                'Fetch Live Data',
                id='fetch-button',
                n_clicks=0,
                style={
                    'marginTop': '0.5rem',
                    'padding': '0.5rem',
                    'background': f'linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]})',
                    'border': 'none',
                    'color': 'white',
                    'borderRadius': '4px',
                    'cursor': 'pointer',
                    'fontWeight': '600',
                    'width': '100%',
                    'fontSize': '0.8rem'
                }
            )
        ], style={'marginBottom': '1.25rem'}),
        
        # Option type
        html.Div([
            html.Label("Option Type", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem', 'fontWeight': 600}),
            dcc.RadioItems(
                id='option-type',
                options=[
                    {'label': ' Call', 'value': 'call'},
                    {'label': ' Put', 'value': 'put'}
                ],
                value='call',
                style={'color': COLORS['text'], 'marginTop': '0.25rem', 'fontSize': '0.9rem'},
                labelStyle={'display': 'inline-block', 'marginRight': '1rem'}
            )
        ], style={'marginBottom': '1.25rem'}),
        
        # American vs European
        html.Div([
            html.Label("Exercise Style", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem', 'fontWeight': 600}),
            dcc.RadioItems(
                id='exercise-style',
                options=[
                    {'label': ' American', 'value': True},
                    {'label': ' European', 'value': False}
                ],
                value=True,
                style={'color': COLORS['text'], 'marginTop': '0.25rem', 'fontSize': '0.9rem'},
                labelStyle={'display': 'inline-block', 'marginRight': '1rem'}
            )
        ], style={'marginBottom': '1.25rem'}),
        
        # Sliders
        html.Div([
            html.Label("Steps", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem', 'fontWeight': 600}),
            dcc.Slider(id='num-steps', min=10, max=500, step=10, value=100, marks=None, tooltip={"placement": "bottom", "always_visible": True}, updatemode='drag')
        ], style={'marginBottom': '1.25rem'}),

        html.Div([
            html.Label("Spot Price ($)", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem', 'fontWeight': 600}),
            dcc.Slider(id='spot-price', min=50, max=300, step=1, value=150, marks=None, tooltip={"placement": "bottom", "always_visible": True}, updatemode='drag')
        ], style={'marginBottom': '1.25rem'}),

        html.Div([
            html.Label("Strike Price ($)", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem', 'fontWeight': 600}),
            dcc.Slider(id='strike-price', min=50, max=300, step=1, value=150, marks=None, tooltip={"placement": "bottom", "always_visible": True}, updatemode='drag')
        ], style={'marginBottom': '1.25rem'}),

        html.Div([
            html.Label("Time (Years)", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem', 'fontWeight': 600}),
            dcc.Slider(id='time-to-exp', min=0.01, max=2, step=0.01, value=0.5, marks=None, tooltip={"placement": "bottom", "always_visible": True}, updatemode='drag')
        ], style={'marginBottom': '1.25rem'}),

        html.Div([
            html.Label("Volatility (σ)", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem', 'fontWeight': 600}),
            dcc.Slider(id='volatility', min=0.05, max=1.0, step=0.01, value=0.25, marks=None, tooltip={"placement": "bottom", "always_visible": True}, updatemode='drag')
        ], style={'marginBottom': '1.25rem'}),

        html.Div([
            html.Label("Risk-Free Rate (%)", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem', 'fontWeight': 600}),
            dcc.Slider(id='risk-free-rate', min=0, max=10, step=0.1, value=4.5, marks=None, tooltip={"placement": "bottom", "always_visible": True}, updatemode='drag')
        ], style={'marginBottom': '1.25rem'}),
        
        # Model info
        html.Div([
            html.Div(id='model-info', style={
                'fontSize': '0.75rem',
                'color': COLORS['text_secondary'],
                'lineHeight': '1.4'
            })
        ], style={
            'background': COLORS['background'],
            'borderRadius': '6px',
            'padding': '0.75rem',
            'borderLeft': f'3px solid {COLORS["secondary"]}'
        })

    ], style={
        'width': '320px',
        'minWidth': '320px',
        'background': COLORS['surface'],
        'padding': '1.5rem',
        'height': '100vh',
        'overflowY': 'auto',
        'boxShadow': '2px 0 10px rgba(0,0,0,0.3)',
        'zIndex': 10
    }),
    
    # Main Content Area
    html.Div([
        # Metrics container
        html.Div([
            # Price (Primary)
            html.Div([
                html.H4("Option Price", style={'margin': '0 0 0.25rem 0', 'fontSize': '0.8rem', 'color': COLORS['text_secondary']}),
                html.H2(id='option-price', style={'margin': 0, 'fontSize': '1.8rem', 'color': COLORS['success']})
            ], style={'background': COLORS['surface'], 'padding': '1rem', 'borderRadius': '8px', 'flex': '1', 'marginRight': '1rem', 'borderLeft': f'4px solid {COLORS["success"]}'}),
            
            # Greeks grid
            html.Div([
                html.Div([html.Span("Delta", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem'}), html.Br(), html.Span(id='delta', style={'fontWeight': 'bold', 'color': COLORS['primary']})], style={'flex': 1}),
                html.Div([html.Span("Gamma", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem'}), html.Br(), html.Span(id='gamma', style={'fontWeight': 'bold', 'color': COLORS['primary']})], style={'flex': 1}),
                html.Div([html.Span("Theta", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem'}), html.Br(), html.Span(id='theta', style={'fontWeight': 'bold', 'color': COLORS['danger']})], style={'flex': 1}),
                html.Div([html.Span("Vega", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem'}), html.Br(), html.Span(id='vega', style={'fontWeight': 'bold', 'color': COLORS['success']})], style={'flex': 1}),
                html.Div([html.Span("Rho", style={'color': COLORS['text_secondary'], 'fontSize': '0.8rem'}), html.Br(), html.Span(id='rho', style={'fontWeight': 'bold', 'color': COLORS['primary']})], style={'flex': 1}),
            ], style={'background': COLORS['surface'], 'padding': '1rem', 'borderRadius': '8px', 'flex': '3', 'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'})
        ], style={'display': 'flex', 'marginBottom': '1.5rem'}),
        
        # Visualization area
        html.Div([
            # Tree Visualization (New)
            html.Div([
                dcc.Graph(id='tree-viz', style={'height': '400px'}, config={'displayModeBar': False})
            ], style={'background': COLORS['surface'], 'borderRadius': '8px', 'padding': '1rem', 'marginBottom': '1rem'}),

            # Payoff Diagram
            html.Div([
                dcc.Graph(id='payoff-diagram', style={'height': '350px'}, config={'displayModeBar': False})
            ], style={'background': COLORS['surface'], 'borderRadius': '8px', 'padding': '1rem', 'marginBottom': '1rem'}),
            
            # Greeks Chart (Full Width)
            html.Div([
                dcc.Graph(id='greeks-chart', style={'height': '350px'}, config={'displayModeBar': False})
            ], style={'background': COLORS['surface'], 'borderRadius': '8px', 'padding': '1rem', 'marginBottom': '1rem'}),

            # Volatility Surface (Full Width)
            html.Div([
                dcc.Graph(id='vol-surface', style={'height': '400px'}, config={'displayModeBar': False})
            ], style={'background': COLORS['surface'], 'borderRadius': '8px', 'padding': '1rem'})
        ])
        
    ], style={
        'flex': '1',
        'height': '100vh',
        'overflowY': 'auto',
        'padding': '2rem',
        'background': COLORS['background']
    }),
    
    # Hidden div to store fetched data
    dcc.Store(id='market-data')
    
], style={'display': 'flex', 'height': '100vh', 'overflow': 'hidden', 'fontFamily': 'sans-serif'})

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
     Output('tree-viz', 'figure'),
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
        height=400,
        margin=dict(l=0, r=0, b=0, t=30)
    )
    
    # --- Tree Visualizer ---
    viz_steps = min(steps, 10) # Limit depth for visualization
    tree_nodes = engine.get_tree_structure(S, K, T, r, sigma, is_call, viz_steps, american)
    
    tree_fig = go.Figure()
    
    # Draw edges first (so lines are behind nodes)
    # This is a bit manual since we have a flat list of nodes, but strictly:
    # Node at (step, index) connects to (step+1, index) and (step+1, index+1)
    
    edge_x = []
    edge_y = []
    
    # Helper to find node by step/index
    # Optimization: since tree is small, simple lookup is fine, or math calculation
    # Since nodes are generated in order, we can map (step, index) -> node object
    node_map = {}
    for n in tree_nodes:
        node_map[(n.step, n.index)] = n
        
    for n in tree_nodes:
        if n.step < viz_steps:
            # Connect to up move (step+1, index)
            up_node = node_map.get((n.step + 1, n.index))
            if up_node:
                edge_x.extend([n.step, n.step + 1, None])
                edge_y.extend([n.stock_price, up_node.stock_price, None])
            
            # Connect to down move (step+1, index+1)
            down_node = node_map.get((n.step + 1, n.index + 1))
            if down_node:
                edge_x.extend([n.step, n.step + 1, None])
                edge_y.extend([n.stock_price, down_node.stock_price, None])
                
    tree_fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(color='rgba(255, 255, 255, 0.2)', width=1),
        hoverinfo='none',
        showlegend=False
    ))
    
    # Draw nodes
    node_x = [n.step for n in tree_nodes]
    node_y = [n.stock_price for n in tree_nodes]
    node_vals = [n.option_value for n in tree_nodes]
    node_text = [
        f"Step: {n.step}<br>Spot: ${n.stock_price:.2f}<br>Option: ${n.option_value:.2f}" 
        for n in tree_nodes
    ]
    
    # Highlight early exercise nodes (approximate logic for visual flair)
    # Exact check would need comparison with intrinsic
    marker_colors = []
    intrinsic_vals = []
    for n in tree_nodes:
        intrinsic = max(n.stock_price - K, 0) if is_call else max(K - n.stock_price, 0)
        # Floating point tolerance
        if american and n.option_value > 0 and abs(n.option_value - intrinsic) < 0.001 and n.step < viz_steps:
             marker_colors.append(COLORS['success']) # Green for exercise
        else:
             marker_colors.append(COLORS['primary']) # Blue for continuation
    
    tree_fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        marker=dict(
            size=10,
            color=marker_colors,
            line=dict(color='white', width=1)
        ),
        text=node_text,
        hoverinfo='text',
        name='Nodes'
    ))
    
    tree_fig.update_layout(
        title=f"Binomial Tree Structure (First {viz_steps} Steps)",
        xaxis_title="Step",
        yaxis_title="Stock Price ($)",
        paper_bgcolor=COLORS['surface'],
        plot_bgcolor=COLORS['background'],
        font=dict(color=COLORS['text']),
        showlegend=False,
        margin=dict(l=40, r=40, b=40, t=40)
    )

    return (price_text, delta_text, gamma_text, theta_text, vega_text, rho_text,
            model_info_text, tree_fig, payoff_fig, greeks_fig, vol_fig)

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