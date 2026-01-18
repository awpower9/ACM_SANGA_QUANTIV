import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np
import time  # <--- 1. NEW IMPORT

# --- ENGINE IMPORTS ---
try:
    import quantiv_engine
    # Initialize engines once globally
    binomial_engine = quantiv_engine.BinomialEngine()
    bsm_engine = quantiv_engine.BlackScholes()
    USE_CPP = True
except ImportError:
    USE_CPP = False
    print("⚠ C++ Engine not found.")

# --- KEEPING YOUR EXISTING GRAPH LOGIC ---
import pages.graphs as graphs 

dash.register_page(__name__, path='/models')

layout = html.Div([
    
    # --- LEFT SIDE: CONTROLS ---
    html.Div([      
          html.Div([
              html.P("Select Model", style={"fontSize":"25px", "padding":"0 10px"}),
              dcc.Dropdown(
                  id="model1-selector",
                  options=[
                     {"label":"Black-Scholes", "value":"BlackScholes"},
                     {"label":"Binomial Option model", "value":"binomial"},
                     {"label":"Trinomial option model", "value":"trinomial"}
                  ],
                  value="BlackScholes", clearable=False
              )
          ], className="models1"),
          
          html.Div([
                html.P("Option Type", style={"margin":"20px 25px", "fontSize":"30px"}),
                dcc.RadioItems(
                    id='option-type',
                    options=[
                        {"label":"Call", "value":"call"},
                        {"label":"Put", "value":"put"}
                    ], value="call", 
                    style={"display":"flex", "justifyContent":"space-evenly", "width":"10vw"}
                ),
                
                html.P("Exercise Style", style={"margin":"20px 25px", "fontSize":"30px"}),
                dcc.RadioItems(
                    id='option-style',
                    options=[
                        {"label":"European", "value":"european"},
                        {"label":"American", "value":"american"}
                    ], value="american", 
                    style={"display":"flex", "justifyContent":"space-evenly", "width":"14vw"}
                )
          ], className="extra")
    ]),

    # --- CENTER: GRAPH ---
    html.Div([
        dcc.Loading(
            id="loading-graph",
            type="circle",
            color="#00ff88",
            children=dcc.Graph(
                id="main-graph", 
                style={'height': '100%'},
                config={'displayModeBar': False}
            )
        )
    ], className="graph-card", style={
        "width": "50vw", 
        "margin": "40px 10px",
        "height": "80vh"
    }),

    # --- RIGHT: SLIDERS ---
    html.Div([
         html.Div([
            html.Label("Stock Price ($)", style={'color':'white'}),
            dcc.Slider(id='S', min=50, max=150, value=100, tooltip={'always_visible':True},marks=None, className="slider"),
    
            html.Label("Strike Price ($)", style={'color':'white'}),
            dcc.Slider(id="K", min=50, max=150, value=100, tooltip={'always_visible':True},marks=None, className="slider"),
    
            html.Label("Volatility (σ)", style={'color':'white'}),
            dcc.Slider(id="v", min=0.1, max=1.0, step=0.05, value=0.2, tooltip={'always_visible':True},marks=None, className="slider"),
    
            html.Label("Time (Years)", style={'color':'white'}),
            dcc.Slider(id="t", min=0.1, max=5, step=0.1, value=1, tooltip={'always_visible':True},marks=None, className="slider"),
    
            html.Label("Steps (N)", style={'color':'white'}),
            dcc.Slider(id="N", min=1, max=20, step=1, value=5, tooltip={'always_visible':True},marks=None, className="slider"),
         ], className='sliders', style={'width': '100%', 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-evenly', 'height': '60%'}),
   
         html.Div([
             html.Label("Calculated Option Price", style={"margin":"0", "fontSize":"18px", "color":"#888"}),
             html.Div(id="option-price", style={"fontSize": "40px", "color": "#00ff88", "fontWeight": "bold"})
         ], className='optionprice', style={'width': '100%', 'marginTop': '20px', 'textAlign': 'center'})
         
   ], className="inputs", style={"width": "24vw", "margin": "auto 10px"})
   
], style={'display':'flex', 'justifyContent':'center', 'alignItems': 'center', 'height': '100vh', 'width': '100vw', 'overflow': 'hidden'})


# --- MAIN CALLBACK ---
@callback(
    [Output("option-price", "children"),
     Output("main-graph", "figure"),
     Output("shared-store", "data")],
    
    [Input("S", "value"),
     Input("K", "value"),
     Input("v", "value"),
     Input("t", "value"),
     Input("N", "value"),
     Input("option-type", "value"),
     Input("option-style", "value"),
     Input("model1-selector", "value")]
)
def update_dashboard(S, K, sigma, T, steps, option_type_str, option_style, model_name):
    # 1. Setup Variables
    r = 0.05 
    is_call = (option_type_str == 'call')
    american = (option_style == 'american') 
    
    # Safe Inputs
    S = float(S) if S else 100.0
    K = float(K) if K else 100.0
    sigma = float(sigma) if sigma else 0.2
    T = float(T) if T else 1.0
    steps = int(steps) if steps else 5

    price_text = "$0.00"
    fig = go.Figure()

    # 2. Logic Per Model
    if model_name == "binomial":    
        if USE_CPP:
            result = binomial_engine.calculate_option(S, K, T, r, sigma, is_call, steps, american)
            price_text = f"${result.price:.2f}"
            
            # Use your existing graph logic
            viz_nodes = binomial_engine.get_tree_structure(S, K, T, r, sigma, is_call, steps, american)
            fig = graphs.draw_binomial_tree(viz_nodes, steps)
        else:
             price_text = "Error: Engine Not Loaded"
        
    elif model_name == "BlackScholes":
        if USE_CPP:
            result = bsm_engine.calculate(S, K, T, sigma, is_call)
            price_text = f"${result.price:.2f}"
            
            # Simple Visual for BS
            fig.add_annotation(
                text="Black-Scholes Model<br>(Exact Formula)",
                xref="paper", yref="paper", x=0.5, y=0.5, 
                showarrow=False, font={'color':'white', 'size': 24}
            )
            fig.update_layout(
                plot_bgcolor='black', paper_bgcolor='black',
                xaxis={'visible': False}, yaxis={'visible': False}
            )
        
    elif model_name == "trinomial":
        price_text = "$0.00"
        fig.add_annotation(text="Trinomial Model<br>(Coming Soon)", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font={'color':'white'})
        fig.update_layout(plot_bgcolor='black', paper_bgcolor='black', xaxis={'visible': False}, yaxis={'visible': False})
        
    # 3. Save Data (WITH TIMESTAMP)
    store_data = {
        'model': model_name,
        'type': option_type_str, 'style': option_style,
        'S': S, 'K': K, 'v': sigma, 't': T, 'N': steps, 
        'r': r, 
        'price': price_text,
        'timestamp': time.time()  # <--- 2. ADDED TIMESTAMP
    }
    
    return price_text, fig, store_data