import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import numpy as np

# Import our new visualization module
import pages.graphs as graphs

dash.register_page(__name__)

try:
    import binomial_engine
    engine = binomial_engine.BinomialEngine()
    USE_CPP = True
    print("✓ Using C++ binomial engine")
except ImportError:
    USE_CPP = False
    print("⚠ C++ engine not available, using Python fallback")


class PythonBinomialEngine:
    def binomial_price(self, S, K, T, r, sigma, is_call, steps, american=True):
        if T <= 0 or steps <= 0: return max(S - K, 0) if is_call else max(K - S, 0)
        dt = T / steps
        u = np.exp(sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp(r * dt) - d) / (u - d)
        discount = np.exp(-r * dt)
        
        # Initialize option values at maturity
        option_values = np.zeros(steps + 1)
        for i in range(steps + 1):
            ST = S * (u ** (steps - i)) * (d ** i)
            option_values[i] = max(ST - K, 0) if is_call else max(K - ST, 0)
        for j in range(steps - 1, -1, -1):
            for i in range(j + 1):
                option_values[i] = discount * (p * option_values[i] + (1 - p) * option_values[i + 1])
                if american:
                    stock_price = S * (u ** (j - i)) * (d ** i)
                    option_values[i] = max(option_values[i], (max(stock_price - K, 0) if is_call else max(K - stock_price, 0)))
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

layout = html.Div([
    
    # Left section
    html.Div([
        html.P("Select Model", style={"font-size":"25px","padding":"0 10px", "color": "white"}),
        dcc.Dropdown(
            id='model-selector',
            options=[
               {"label":"Black Scholes", "value":"BlackScholes"},
               {"label":"Binomial Model", "value":"binomial"},
               {"label":"Trinomial Model", "value":"trinomial"}
            ],
            value="binomial",
            clearable=False
        )
    ], className="models1", style={
        "width": "15vw", 
        "margin": "40px 10px",
        "height": "80vh" # Taller to match others
    }),

    # Center section
    html.Div([
        dcc.Loading(
            id="loading-graph",
            type="circle",
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

    # Right section
    html.Div([
         html.Div([
            html.Label(f"Stock Price ($)", style={'margin':'10px 0', 'color':'white'}),
            dcc.Slider(id='S', min=50, max=150, value=100, marks=None, tooltip={'always_visible':True}, className="slider"),
    
            html.Label(f"Strike Price ($)", style={'margin':'10px 0', 'color':'white'}),
            dcc.Slider(id="K", min=50, max=150, value=100, marks=None, tooltip={'always_visible':True}, className="slider"),
    
            html.Label(f"Volatility (σ)", style={'margin':'10px 0', 'color':'white'}),
            dcc.Slider(id="v", min=0.1, max=1.0, step=0.05, value=0.2, marks=None, tooltip={'always_visible':True}, className="slider"),
    
            html.Label(f"Time (Years)", style={'margin':'10px 0', 'color':'white'}),
            dcc.Slider(id="t", min=0.1, max=5, step=0.1, value=1, marks=None, tooltip={'always_visible':True}, className="slider"),
    
            html.Label(f"Steps (High = Slow)", style={'margin':'10px 0', 'color':'white'}),
            dcc.Slider(id="N", min=10, max=100, step=10, value=20, marks=None, tooltip={'always_visible':True}, className="slider"),
            
            html.Div([
                html.Label("Option Type", style={'color':'white', 'marginRight':'10px'}),
                dcc.RadioItems(
                    id='option-type',
                    options=[{'label': 'Call', 'value': 'call'}, {'label': 'Put', 'value': 'put'}],
                    value='call',
                    labelStyle={'display': 'inline-block', 'marginRight':'10px', 'color':'white'}
                )
            ], style={'marginTop': '20px'}),

         ], className='sliders', style={'width': '100%'}),
         
         html.Div([
             html.Label("Calculated Option Price", style={"margin":"0", "font-size":"18px", "color":"#888"}),
             html.Div(id="option-price", style={"fontSize": "40px", "color": "#00ff88", "fontWeight": "bold"})
         ], className='optionprice', style={'width': '100%', 'marginTop': '20px'})
         
   ], className="inputs", style={
       "width": "24vw",
       "margin": "auto 10px"
   })
   
], style={'display':'flex', 'justify-content':'center', 'alignItems': 'center', 'height': '100vh', 'width': '100vw', 'overflow': 'hidden', 'padding': '0', 'margin': '0'})

@callback(
    [Output("option-price", "children"),
     Output("main-graph", "figure")],
    [Input("S", "value"),
     Input("K", "value"),
     Input("v", "value"),
     Input("t", "value"),
     Input("N", "value"),
     Input("option-type", "value")]
)
def update_dashboard(S, K, sigma, T, steps, option_type_str):
    r = 0.05
    is_call = (option_type_str == 'call')
    american = True # Default for now
    
    # Calculate Price
    result = engine.calculate_option(S, K, T, r, sigma, is_call, steps, american)
    price_text = f"${result.price:.2f}"
    
    # Gets tree nodes and draw graph
    viz_nodes = engine.get_tree_structure(S, K, T, r, sigma, is_call, steps, american)
    fig = graphs.draw_binomial_tree(viz_nodes, steps)
        
    return price_text, fig

