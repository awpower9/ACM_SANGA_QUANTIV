import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
import math
import time  # <--- Required for synchronization

# --- SAFETY IMPORT ---
try:
    import quantiv_engine
    C_ENGINE_AVAILABLE = True
except ImportError:
    C_ENGINE_AVAILABLE = False
    print("⚠️ C++ Engine failed to import. Using Python backup.")

dash.register_page(__name__)

SLIDER_STYLE = {'marginBottom': '15px'}
LABEL_STYLE = {'color': "#eef3f4", 'fontWeight': 'bold', 'fontSize': '14px', "marginLeft": "100px"}

layout = html.Div([
    dcc.Location(id='advmodels-url', refresh=False), # LISTENS TO URL
    # --- Store for this page ---
    # We use storage_type='session' so data persists when navigating to Greeks
 
    
    # --- LEFT SIDE ---
    html.Div([  
        html.Div([
            html.P("Select Model", style={"fontSize":"25px", "padding":"0 10px", "color": "white"}),
            dcc.Dropdown(
                id="adv_model_selector",
                options=[
                    {"label":"Merton Jump Diffusion", "value":"Merton"},
                    {"label":"Heston Stochastic Volatility", "value":"Heston"},
                ],
                value="Merton",
                clearable=False,
                style={'color': 'white'}
            )
        ], className="models2", style={'marginBottom': '20px', "color": "white"}),

        html.Div([
            html.P("Jump Parameters", style={"fontSize":"20px", "color": "#ff9900", "textAlign": "center"}),
            html.Label("Jump Freq (λ)", style=LABEL_STYLE),
            dcc.Slider(id='lambda', min=0, max=5, value=1, step=0.5, marks=None, tooltip={'always_visible':True}, className="slider"),
            html.Label("Mean Jump Size (μ)", style=LABEL_STYLE),
            dcc.Slider(id="mu_j", min=-0.5, max=0.5, value=-0.1, step=0.05, marks=None, tooltip={'always_visible':True}, className="slider"),
            html.Label("Jump Volatility (δ)", style=LABEL_STYLE),
            dcc.Slider(id="delta_j", min=0.0, max=0.5, value=0.1, step=0.05, marks=None, tooltip={'always_visible':True}, className="slider"),
        ], className="extra", style={'padding': '10px', 'backgroundColor': '#1a1a1a', 'borderRadius': '10px'}),
       
        html.Div([
            html.P("Option Settings", style={"fontSize":"20px", "marginLeft":"20px", "color": "white", "marginTop": "20px"}),
            dcc.RadioItems(
                id="adv_option_type",
                options=[
                    {"label": "Call Option", "value": "call"},
                    {"label": "Put Option", "value": "put"}
                ],
                value="call",
                style={"display":"flex", "justifyContent":"space-evenly", "width":"100%", "color": "white"}
            )
        ], className="callput")
    ], style={'width': '25vw', 'padding': '20px'}),

    # --- CENTER ---
    html.Div([
        dcc.Graph(id="adv_main_graph", style={'height': '100%', 'width': '100%', 'backgroundColor': 'transparent'})
    ], style={"margin":"100px 10px", "backgroundColor":"black", "width":"50vw", 'height':'75vh', 'borderRadius':'30px', 'padding':'10px', 'border': '1px solid #333'}, className="tree"),
   
    # --- RIGHT SIDE ---
    html.Div([
         html.Div([
            html.Label("Stock Price", style={'color':'white', "marginLeft": "130px"}),
            dcc.Slider(id='S1', min=50, max=150, value=100, marks=None, tooltip={'always_visible':True}, className="slider"),
            html.Label("Strike Price", style={'color':'white', "marginLeft": "130px"}),
            dcc.Slider(id="K1", min=50, max=150, value=100, marks=None, tooltip={'always_visible':True}, className="slider"),
            html.Label("Volatility", style={'color':'white', "marginLeft": "130px"}),
            dcc.Slider(id="v2", min=0.1, max=1.0, value=0.2, marks=None, tooltip={'always_visible':True}, className="slider"),
            html.Label("Time", style={'color':'white', "marginLeft": "130px"}),
            dcc.Slider(id="t2", min=0.1, max=5, value=1, step=0.1, marks=None, tooltip={'always_visible':True}, className="slider"),
         ], className='sliders', style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-evenly', 'height': '60%'}),
         
         html.Div([
             html.Label("Calculated Price", style={"fontSize":"18px", "color": "#888"}),
             html.Div(id="adv_price_display", style={"fontSize": "40px", "color": "#00ff88", "fontWeight": "bold"})
         ], className='optionprice', style={'textAlign': 'center', 'marginTop': '20px'})
   ], className="inputs", style={'width': '20vw', 'marginRight': '20px'})

], style={'display':'flex', 'justifyContent':'space-evenly', 'backgroundColor': 'transparent', 'height': '100vh', "width":"97vw"})

# --- PYTHON FALLBACK ---
def python_merton(S, K, T, r, sigma, lam, mu, delta, is_call):
    if T <= 0: return max(0.0, S - K) if is_call else max(0.0, K - S)
    k = math.exp(mu + 0.5 * delta**2) - 1
    lambda_p = lam * (1 + k)
    price = 0.0
    for n in range(15):
        fact = math.factorial(n)
        weight = (math.exp(-lambda_p * T) * (lambda_p * T)**n) / fact
        sigma_n = math.sqrt(sigma**2 + (n * delta**2) / T)
        r_n = r - lam * k + (n * math.log(1 + k)) / T
        d1 = (math.log(S/K) + (r_n + 0.5 * sigma_n**2) * T) / (sigma_n * math.sqrt(T))
        d2 = d1 - sigma_n * math.sqrt(T)
        def N(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
        bs = (S * N(d1) - K * math.exp(-r_n * T) * N(d2)) if is_call else (K * math.exp(-r_n * T) * N(-d2) - S * N(-d1))
        price += weight * bs
    return price

def python_bsm(S, K, T, r, sigma, is_call):
    d1 = (math.log(S/K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    def N(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    return (S * N(d1) - K * math.exp(-r * T) * N(d2)) if is_call else (K * math.exp(-r * T) * N(-d2) - S * N(-d1))

# --- CALLBACK ---
@callback(
    [Output("adv_price_display", "children"),
     Output("adv_main_graph", "figure"),
     # FIX: Removed allow_duplicate=True since this store is now unique to this page
     Output("shared-store2", "data")],
    [Input("adv_model_selector", "value"),
     Input("S1", "value"), Input("K1", "value"), 
     Input("v2", "value"), Input("t2", "value"),
     Input("adv_option_type", "value"),
     Input("lambda", "value"), Input("mu_j", "value"), Input("delta_j", "value")],
     # FIX: Removed prevent_initial_call so data saves immediately on load
)
def update_advanced_calculations(model, S, K, v, T, option_type, lam, mu, delta):
    
    r = 0.05
    is_call = (option_type == "call")
    price = 0.0

    S = float(S) if S else 100.0
    K = float(K) if K else 100.0
    v = float(v) if v else 0.2
    T = float(T) if T else 1.0
    lam = float(lam) if lam is not None else 1.0
    mu = float(mu) if mu is not None else -0.1
    delta = float(delta) if delta is not None else 0.1

    fig = go.Figure()

    x_range = np.linspace(max(1, S*0.5), S*1.5, 50)
    y_vals = []
    y_bsm = []

    used_python = False
    
    # 
    if C_ENGINE_AVAILABLE:
        try:
            bsm_engine = quantiv_engine.BlackScholes()
            
            if model == "Merton":
                merton_engine = quantiv_engine.Merton()
                res = merton_engine.calculate(S, K, T, r, v, lam, mu, delta, is_call)
                price = res.price
                for x in x_range:
                    y_vals.append(merton_engine.calculate(float(x), K, T, r, v, lam, mu, delta, is_call).price)
                    y_bsm.append(bsm_engine.calculate(float(x), K, T, v, is_call).price)

            elif model == "Heston":
                heston_engine = quantiv_engine.Heston()
                # Heston params: kappa (mean rev), theta (long var), xi (vol of vol), rho (corr)
                # Using slider mappings: 
                # lam -> kappa, mu -> theta, delta -> xi. We need rho (default -0.5)
                # For now mapping: lam->kappa, mu->theta (scaled?), delta->xi
                # Let's use the sliders as is:
                kappa = lam  # 0-5
                theta = abs(mu) # 0-0.5 (approx)
                xi = delta # 0-0.5
                rho = -0.5 # Constant for now or add slider later
                v0 = theta # Start at long term mean
                
                res = heston_engine.calculate(S, K, T, r, kappa, theta, xi, rho, v0, is_call)
                price = res.price
                for x in x_range:
                    y_vals.append(heston_engine.calculate(float(x), K, T, r, kappa, theta, xi, rho, v0, is_call).price)
                    y_bsm.append(bsm_engine.calculate(float(x), K, T, math.sqrt(theta), is_call).price)

        except Exception as e:
            print(f"C++ Engine Error: {e}")
            used_python = True
    else:
        used_python = True

    if used_python:
        print("Calculating with Python...")
        price = python_merton(S, K, T, r, v, lam, mu, delta, is_call)
        for x in x_range:
            y_vals.append(python_merton(x, K, T, r, v, lam, mu, delta, is_call))
            y_bsm.append(python_bsm(x, K, T, r, v, is_call))
    
    # Plotting
    if len(y_vals) > 0:
        fig.add_trace(go.Scatter(x=x_range, y=y_vals, mode='lines', name=f'{model} Model', line=dict(color='white', width=2)))
    if len(y_bsm) > 0:
        fig.add_trace(go.Scatter(x=x_range, y=y_bsm, mode='lines', name='Black-Scholes', line=dict(color='violet', width=2)))
    fig.add_trace(go.Scatter(x=[S], y=[price], mode='markers', marker=dict(color='white', size=10), showlegend=False))

    fig.update_layout(
        title={'text': f"{model} vs Black-Scholes", 'font': {'size': 20, 'color': 'white'}},
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        xaxis={'title': 'Stock Price ($)', 'gridcolor': '#333'},
        yaxis={'title': 'Option Price ($)', 'gridcolor': '#333'},
        legend={'x': 0.05, 'y': 0.95, 'bgcolor': 'rgba(0,0,0,0.5)'},
        margin=dict(l=40, r=40, t=60, b=40)
    )

    # --- SAVE DATA ---
    store_data = {
        'model': 'merton' if model == 'Merton' else 'blackscholes',
        'type': option_type, 
        'style': 'european',
        'S': S, 'K': K, 'v': v, 't': T,
        'lambda': lam, 'mu': mu, 'delta': delta, 'price': f"${price:.2f}",
        'timestamp': time.time()  # <--- CRITICAL FOR GREEKS PAGE SYNC
    }

    return f"${price:.2f}", fig, store_data


# --- URL PARSING CALLBACK ---
@callback(
    Output("adv_model_selector", "value"),
    Input("advmodels-url", "search")
)
def update_adv_model_dropdown_from_url(search):
    if not search:
        return dash.no_update
    
    if "model=" in search:
        try:
            params = search.split("model=")[1].split("&")[0]
            # URL: Merton -> Dropdown: Merton
            # URL: Heston -> Dropdown: Heston
            return params
        except IndexError:
            return dash.no_update
    
    return dash.no_update