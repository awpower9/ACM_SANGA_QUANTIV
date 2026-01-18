import dash
from dash import dcc, html, callback, ctx
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
import math
import datetime

# --- SAFETY IMPORT ---
try:
    import quantiv_engine
except ImportError:
    pass

dash.register_page(__name__)

layout = html.Div([
      # --- CRITICAL: Declare BOTH stores here so this page can see them ---
 # Advanced Page Data

      html.Div([
           html.Div([
               dcc.Graph(id="graph-option-stock", style={"width":"35vw","height":"45vh"}, className="graph1s"),
           ], className="Scholes"),
           
           html.Div([
               html.Div([
                   dcc.Graph(id="graph-delta-stock", style={"height":"22vh"}, className="graph1s"),
                   ], className="greeks"),
               
               html.Div([
                   dcc.Graph(id="graph-vega-volatility", className="graph1s", style={"height":"22vh"}),
                   ], className="greeks") 
                 
           ], className="greek1"),

           html.Div([
               html.Div([
                   dcc.Graph(id="graph-gamma-stock", className="graph1s", style={"height":"22vh"}),
                   ], className="greeks"),
               
               html.Div([
                   dcc.Graph(id="graph-theta-time", className="graph1s", style={"height":"22vh"}),
                   ], className="greeks")
               
           ], className="greek1")
      ], className="greeks_container"),
      
      # --- DEBUG INFO DISPLAY (To verify data flow) ---
      html.Div(id="greeks-debug-info", style={'textAlign': 'center', 'color': 'gray', 'marginTop': '20px'})
])

# --- 1. PRICING HELPER ---
def get_price(engine, model_name, S, K, T, r, v, is_call, N, is_american, lam, mu, delta):
    if T <= 0: return max(0.0, S - K) if is_call else max(0.0, K - S)
    
    try:
        if engine:
            name = model_name.lower()
            if name == "merton":
                return engine.calculate(float(S), float(K), float(T), r, float(v), float(lam), float(mu), float(delta), is_call).price
            elif name == "blackscholes":
                return engine.calculate(float(S), float(K), float(T), float(v), is_call).price
            else:
                return engine.calculate_option(float(S), float(K), float(T), r, float(v), is_call, N, is_american).price
    except:
        pass 
    
    # Python Fallback
    return 0.0

# --- 2. FINITE DIFFERENCE GREEKS ---
class FiniteDiffResult:
    def __init__(self, engine, model, S, K, T, r, v, is_call, N, amer, l, m, d):
        self.price = get_price(engine, model, S, K, T, r, v, is_call, N, amer, l, m, d)
        
        # Delta/Gamma
        ds = S * 0.01
        p_up = get_price(engine, model, S+ds, K, T, r, v, is_call, N, amer, l, m, d)
        p_down = get_price(engine, model, S-ds, K, T, r, v, is_call, N, amer, l, m, d)
        self.delta = (p_up - p_down) / (2 * ds)
        self.gamma = (p_up - 2*self.price + p_down) / (ds**2)
        
        # Vega
        dv = 0.01
        p_v_up = get_price(engine, model, S, K, T, r, v+dv, is_call, N, amer, l, m, d)
        self.vega = (p_v_up - self.price) / (dv * 100)
        
        # Theta
        dt = 1/365.0
        if T > dt:
            p_t_down = get_price(engine, model, S, K, T-dt, r, v, is_call, N, amer, l, m, d)
            self.theta = (p_t_down - self.price)
        else:
            self.theta = 0.0

# --- CALLBACK ---
@callback(
    [Output("graph-option-stock","figure"),
     Output("graph-delta-stock","figure"),
     Output("graph-gamma-stock","figure"),
     Output("graph-vega-volatility","figure"),
     Output("graph-theta-time","figure"),
     Output("greeks-debug-info", "children")], # Update debug text
    [Input("shared-store", "data"),
     Input("shared-store2", "data")]
)
def update_greeks_graphs(data_std, data_adv):
    
    # --- DATA SELECTION LOGIC ---
    t_std = data_std.get('timestamp', 0) if data_std else 0
    t_adv = data_adv.get('timestamp', 0) if data_adv else 0
    
    
   
    source="unknown"
    # Prefer newer data
    if t_adv > t_std and data_adv:
        data = data_adv
        source = "Advanced Models Page"
    elif data_std:
        data = data_std
        source = "Standard Models Page"
    elif data_adv:
        data = data_adv
        source = "Advanced Models Page"
    else:
        empty = go.Figure()
        empty.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return empty, empty, empty, empty, empty, "No Data Loaded"

    # Extract Data
    model_name = str(data.get('model', 'binomial'))
    S0 = float(data.get('S', 100))
    K = float(data.get('K', 100))
    v0 = float(data.get('v', 0.2))
    T0 = float(data.get('t', 1.0))
    r, N = 0.05, int(data.get('N', 50))
    is_call = (str(data.get('type')).lower() != 'put')
    is_american = (str(data.get('style')).lower() == 'american')
    lam = float(data.get('lambda', 1.0))
    mu = float(data.get('mu', -0.1))
    delta = float(data.get('delta', 0.1))
    
     # Block unsupported advanced models
    if source == "Advanced Models Page" and model_name.lower() != "merton":
        empty = go.Figure()
        empty.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return empty, empty, empty, empty, empty, "Only Merton model supported for Greeks"

    # Debug Message
    timestamp_str = datetime.datetime.fromtimestamp(max(t_std, t_adv)).strftime('%H:%M:%S')
    debug_msg = f"Using Data from: {source} | Model: {model_name} | Last Update: {timestamp_str}"

    # Engine Init
    engine = None
    try:
        if model_name.lower() == "merton": engine = quantiv_engine.Merton()
        elif model_name.lower() == "blackscholes": engine = quantiv_engine.BlackScholes()
        else: engine = quantiv_engine.BinomialEngine()
    except Exception as e:
         print("Engine error:", e)

    # --- PLOT GENERATION ---
    def make_curves(x_range, param_name):
        x_vals, y_vals = [], []
        # Optimization: Reduce points for speed if needed (30 is usually fine)
        for x in x_range:
            # Swap the varying parameter
            s_ = x if param_name == 'S' else S0
            v_ = x if param_name == 'v' else v0
            t_ = x if param_name == 't' else T0
            
            res = FiniteDiffResult(engine, model_name, s_, K, t_, r, v_, is_call, N, is_american, lam, mu, delta)
            
            if param_name == 'S': 
                x_vals.append(x); y_vals.append([res.price, res.delta, res.gamma])
            elif param_name == 'v':
                x_vals.append(x); y_vals.append(res.vega)
            elif param_name == 't':
                x_vals.append(x); y_vals.append(res.theta)
        return x_vals, y_vals

    # 1. Stock Price Scenarios
    s_range = np.linspace(max(1, S0*0.5), S0*1.5, 30)
    _, s_results = make_curves(s_range, 'S')
    prices = [p[0] for p in s_results]
    deltas = [p[1] for p in s_results]
    gammas = [p[2] for p in s_results]

    # 2. Volatility Scenarios
    v_range = np.linspace(0.01, 1.0, 30)
    _, vegas = make_curves(v_range, 'v')

    # 3. Time Scenarios
    t_range = np.linspace(0.01, T0, 30)
    _, thetas = make_curves(t_range, 't')

    # Current Point
    curr = FiniteDiffResult(engine, model_name, S0, K, T0, r, v0, is_call, N, is_american, lam, mu, delta)

    # Plotter
    def plot(x, y, title, xl, col, cx, cy):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines', line=dict(color=col, width=3)))
        fig.add_trace(go.Scatter(x=[cx], y=[cy], mode='markers', marker=dict(color='white', size=8)))
        fig.update_layout(title={'text': title, 'font': {'size': 14, 'color': 'white'}},
                          xaxis=dict(title=xl, showgrid=False, color='white'),
                          yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='white'),
                          margin=dict(l=20, r=20, t=40, b=20),
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
        return fig

    return (
        plot(s_range, prices, "Option Price vs Stock", "Stock Price", "#bf00ff", S0, curr.price),
        plot(s_range, deltas, "Delta vs Stock", "Stock Price", "#9b2ee4", S0, curr.delta),
        plot(s_range, gammas, "Gamma vs Stock", "Stock Price", "#8a2ae4", S0, curr.gamma),
        plot(v_range, vegas, "Vega vs Volatility", "Volatility", "#8e1fe3", v0, curr.vega),
        plot(t_range, thetas, "Theta vs Time", "Time (Yrs)", "#9526f0", T0, curr.theta),
        debug_msg
    )