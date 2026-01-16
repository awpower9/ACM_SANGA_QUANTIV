import dash
from dash import dcc,html,callback
from dash.dependencies import Input,Output
import plotly.graph_objects as go

dash.register_page(__name__)

layout=html.Div([


    html.Div([  
             html.Div([
                 html.P("Select Model",style={"font-size":"25px","padding":"0 10px"}),
                 dcc.Dropdown(
                     options=[
                        {"label":"Merton jump diffusion model","value":"Merton"},
                        {"label":"Heston Stochastic Volatility Model","value":"Heston"},
                         ],
                     value="Merton"
                 )
             ],className="models2"),

             html.Div([
                   html.P("Jump diffusion parameters",style={"padding":"10px","font-size":"20px"}),

                   html.Label("Stockprice",style={'margin':'10px 60px'}),
                   dcc.Slider(id='Sa',min=50,max=150,value=100,marks=None,tooltip={'always_visible':True},className="slider"),
           
                   html.Label("Strike price",style={'margin':'10px 60px'}),
                   dcc.Slider(id="Ka",min=50,max=150,value=100,marks=None,tooltip={'always_visible':True},className="slider"),
           
                   html.Label("Volatility",style={'margin':'10px 60px'}),
                   dcc.Slider(id="va",min=0.1,max=1.0,value=0.2,marks=None,tooltip={'always_visible':True},className="slider"),
    
                
             ],className="extra"),
             
             html.Div([
                 html.P("Options",style={"font-size":"20px","margin-left":"20px"}),
                 dcc.RadioItems(
                     options=[
                         {"label":"call option","value":"call"},
                         {"label":"put option","value":"put"}
                 ],style={"display":"flex","justify-content":"space-evenly","width":"15vw"})
             ],className="callput")
           ]),

    html.Div([],style={"margin":"80px 10px","background-color":"black","width":"60vw",'height':'75vh','border-radius':'30px','padding':'10px'},className="tree"),
   
   
    html.Div([
         html.Div([
            html.Label("Stockprice",style={'margin':'10px 100px'}),
            dcc.Slider(id='S',min=50,max=150,value=100,marks=None,tooltip={'always_visible':True},className="slider"),
    
            html.Label("Strike price",style={'margin':'10px 100px'}),
            dcc.Slider(id="K",min=50,max=150,value=100,marks=None,tooltip={'always_visible':True},className="slider"),
    
            html.Label("Volatility",style={'margin':'10px 100px'}),
            dcc.Slider(id="v",min=0.1,max=1.0,value=0.2,marks=None,tooltip={'always_visible':True},className="slider"),
    
            html.Label("Time",style={'margin':'10px 100px'}),
            dcc.Slider(id="t",min=1,max=10,value=2,step=1,marks=None,tooltip={'always_visible':True},className="slider"),
    
            html.Label("Steps",style={'margin':'10px 100px'}),
            dcc.Slider(id="N",min=1,max=10,value=2,step=1,marks=None,tooltip={'always_visible':True},className="slider")
         ],className='sliders') ,  
         html.Div([
             html.Label("Option price",style={"margin":"20px","font-size":"25px"})
         ],className='optionprice')
   ],className="inputs")
],style={'display':'flex','justify-content':'space-between'})

