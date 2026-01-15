import dash
from dash import dcc,html
from dash.dependencies import Input,Output
import plotly.graph_objects as go

app=dash.Dash(__name__,use_pages=True)

navbar = html.Div([
              html.Div([
                html.Img(src="assets/logo1.png",className="logo_png")
              ],className="logo"),

              html.Div([    
                    html.A("Home", href="/",className="nav"),
                    html.A("Models", href="/models",className="nav"),
                    html.A("Advanced Models", href="/advmodels",className="nav"),
                    html.A("Greeks", href="/greeks",className="nav"),
                    html.A("Volatility", href="/volatility",className="nav"),
              ],className="bar"),

              html.Div([],className="credentials"),
              dcc.Store(id='shared-params', storage_type='session')
    ],
    className="navbar"
)

app.layout=html.Div([
  

     navbar,
     dash.page_container
])
if __name__=="__main__":
    app.run(debug=True)