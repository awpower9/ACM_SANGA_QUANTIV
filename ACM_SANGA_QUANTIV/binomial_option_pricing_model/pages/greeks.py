import dash
from dash import dcc,html
from dash.dependencies import Input,Output
import plotly.graph_objects as go

dash.register_page(__name__)

layout=html.Div([


      html.Div([
           html.Div([

           ],className="Scholes"),
           
           
           html.Div([
               html.Div([],className="greeks"),
               html.Div([],className="greeks")   
           ],className="greek1"),

           html.Div([
               html.Div([],className="greeks"),
               html.Div([],className="greeks")
           ],className="greek1")
      ],className="greeks_container")
])

