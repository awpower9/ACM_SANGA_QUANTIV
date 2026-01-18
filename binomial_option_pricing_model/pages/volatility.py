import dash
from dash import dcc,html,callback
from dash.dependencies import Input,Output
import plotly.graph_objects as go
import numpy as np

dash.register_page(__name__)

layout = html.Div([
    html.Div([
        html.Div([
             html.H4("Implied Volatility Surface", style={'color': 'white', 'textAlign': 'center', 'marginBottom': '10px'}),
             dcc.Loading(
                 type="circle",
                 children=dcc.Graph(id='vol-surface-3d', style={'height': '450px','width':'600px'})
             )
        ], className="Scholes"),
           
        html.Div([
             html.H4("Greeks Sensitivity", style={'color': 'white', 'textAlign': 'center', 'marginBottom': '10px'}),
             dcc.Loading(
                 type="circle",
                 children=dcc.Graph(id='vol-greeks-chart', style={'height': '400px','width':'600px'})
             )
        ], className="Scholes"),

    ], className="greeks_container")
])

# Re-using engine logic
try:
    import binomial_engine
    engine = binomial_engine.BinomialEngine()
    USE_CPP = True
except ImportError:
    USE_CPP = False
    class PythonBinomialEngine:
        def binomial_price(self, S, K, T, r, sigma, is_call, steps, american=True):
            if T <= 0 or steps <= 0: return max(S - K, 0) if is_call else max(K - S, 0)
            dt = T / steps
            u = np.exp(sigma * np.sqrt(dt))
            d = 1 / u
            p = (np.exp(r * dt) - d) / (u - d)
            discount = np.exp(-r * dt)
            option_values = np.zeros(steps + 1)
            for i in range(steps + 1):
                ST = S * (u ** (steps - i)) * (d ** i)
                option_values[i] = max(ST - K, 0) if is_call else max(K - ST, 0)
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
            dS = S * 0.01; dSigma = 0.01
            price_up = self.binomial_price(S + dS, K, T, r, sigma, is_call, steps, american)
            price_down = self.binomial_price(S - dS, K, T, r, sigma, is_call, steps, american)
            delta = (price_up - price_down) / (2 * dS)
            gamma = (price_up - 2 * price + price_down) / (dS * dS)
            price_vol_up = self.binomial_price(S, K, T, r, sigma + dSigma, is_call, steps, american)
            vega = (price_vol_up - price) / (dSigma * 100)
            return type('obj', (object,), {'price': price, 'delta': delta, 'gamma': gamma, 'vega': vega})()

    engine = PythonBinomialEngine()


@dash.callback(
    [Output('vol-surface-3d', 'figure'),
     Output('vol-greeks-chart', 'figure')],
    [Input('shared-params', 'data')]
)
def update_volatility_charts(data):
    if not data:
        # Default values if no data in store
        S, K, T, sigma, r, steps = 100, 100, 1, 0.2, 0.05, 50
    else:
        S = data.get('S', 100)
        K = data.get('K', 100)
        T = data.get('T', 1)
        sigma = data.get('sigma', 0.2)
        steps = data.get('steps', 50)
        r = data.get('r', 0.05)
    
    steps = 50 # Force steps for surface performance
    is_call = True
    american = True 
    
    # --- Surface ---
    strikes = np.linspace(K * 0.5, K * 1.5, 20)
    maturities = np.linspace(0.1, 2.0, 20)
    surface = np.zeros((len(maturities), len(strikes)))
    
    for i, mat in enumerate(maturities):
        for j, strike in enumerate(strikes):
            surface[i, j] = engine.binomial_price(S, strike, mat, r, sigma, is_call, steps, american)
            
    vol_fig = go.Figure(data=[go.Surface(
        x=strikes, y=maturities, z=surface,
        colorscale='Viridis', colorbar=dict(title="Price"),
        contours={"z": {"show": True, "start": 0, "end": np.max(surface), "size": 5, "color":"white"}}
    )])
    
    vol_fig.update_layout(
        scene=dict(
            xaxis_title="Strike", yaxis_title="Time", zaxis_title="Price",
            xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
            yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
            zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e4e8ff'), margin=dict(l=0, r=0, b=0, t=0)
    )

    # --- Greeks ---
    spot_range = np.linspace(S * 0.5, S * 1.5, 40)
    deltas, gammas, vegas = [], [], []
    
    for spot in spot_range:
        res = engine.calculate_option(spot, K, T, r, sigma, is_call, steps, american)
        deltas.append(res.delta)
        gammas.append(res.gamma * 100)
        vegas.append(res.vega)
        
    greeks_fig = go.Figure()
    greeks_fig.add_trace(go.Scatter(x=spot_range, y=deltas, name='Delta', line=dict(color='#00d4ff', width=3)))
    greeks_fig.add_trace(go.Scatter(x=spot_range, y=gammas, name='Gamma (×100)', line=dict(color='#7b61ff', width=3)))
    greeks_fig.add_trace(go.Scatter(x=spot_range, y=vegas, name='Vega', line=dict(color='#00ff88', width=3)))
    
    greeks_fig.update_layout(
        xaxis_title="Spot", yaxis_title="Value",
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(20, 27, 61, 0.5)',
        font=dict(color='#e4e8ff'),
        legend=dict(bgcolor='rgba(0,0,0,0)', orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, b=40, t=30)
    )
    greeks_fig.update_xaxes(showgrid=True, gridcolor='rgba(128, 128, 128, 0.2)')
    greeks_fig.update_yaxes(showgrid=True, gridcolor='rgba(128, 128, 128, 0.2)')

    return vol_fig, greeks_fig

