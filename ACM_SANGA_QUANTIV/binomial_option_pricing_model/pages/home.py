import dash
from dash import dcc,html
from dash.dependencies import Input,Output
import plotly.graph_objects as go

dash.register_page(__name__, path="/")

layout=html.Div([

       html.Div([
           html.Div([
               html.Div([
                   html.H1("Quantiv",style={"margin":"60px","font-size":"80px","margin-bottom":"0"}),
                   html.H2("Interactive Option Prcing and Risk Analyitics Platform",style={"margin-left":"68px","margin-top":"0"}),
                   html.H3("Quantiv is a interactive designed to explore option pricing models and risk analytics associated with them",style={"margin-left":"65px","margin-top":"300px"})
               ],className="hometext"),
               html.Div([],style={"width":"40vw"})
            ],className="home1"),
    
        
    ],className="home_container")
])
