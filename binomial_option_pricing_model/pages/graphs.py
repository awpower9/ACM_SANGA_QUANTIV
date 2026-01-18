import plotly.graph_objects as go
import numpy as np

# Color scheme to match the provided UI
COLORS = {
    'background': 'rgba(0,0,0,0)', # Transparent
    'node_call': '#00d4ff',        # Blue
    'node_exercise': '#00ff88',    # Green
    'text': '#ffffff',             # White
    'grid': 'rgba(255,255,255,0.1)' 
}

def draw_binomial_tree(nodes, steps):
    """
    Creates a visual representation of the Binomial Tree.
    """
    fig = go.Figure()
    
    # We limit visualization depth to 15 steps to prevent lag
    viz_steps = min(steps, 15)
    
    # Organize nodes by (step, index) for easy connection
    node_map = {}
    for n in nodes:
        node_map[(n.step, n.index)] = n

    edge_x = []
    edge_y = []
    
    # Create Edges
    for n in nodes:
        if n.step < viz_steps:
            # Connect to "Up" node
            up_node = node_map.get((n.step + 1, n.index))
            if up_node:
                edge_x.extend([n.step, n.step + 1, None])
                edge_y.extend([n.stock_price, up_node.stock_price, None])
            
            # Connect to "Down" node
            down_node = node_map.get((n.step + 1, n.index + 1))
            if down_node:
                edge_x.extend([n.step, n.step + 1, None])
                edge_y.extend([n.stock_price, down_node.stock_price, None])

    # Add Edges to Plot
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(color='rgba(255, 255, 255, 0.3)', width=1),
        hoverinfo='none',
        name='Paths'
    ))

    # Create Nodes
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    
    for n in nodes:
        if n.step <= viz_steps:
            node_x.append(n.step)
            node_y.append(n.stock_price)
            
            txt = f"Step: {n.step}<br>Stock: ${n.stock_price:.2f}<br>Option: ${n.option_value:.2f}"
            node_text.append(txt)
            
            # Color logic
            if n.option_value > 0:
                 node_color.append(COLORS['node_exercise'])
            else:
                 node_color.append(COLORS['node_call'])

    # Add Nodes to Plot
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        marker=dict(size=8, color=node_color, line=dict(color='white', width=1)),
        text=node_text,
        hoverinfo='text',
        name='Nodes'
    ))

    # Styling
    fig.update_layout(
        title={'text': f"Binomial Tree Structure ({viz_steps} Steps)", 'font': {'color': COLORS['text']}},
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['background'],
        xaxis=dict(title='Step', showgrid=False, zeroline=False, color=COLORS['text']),
        yaxis=dict(title='Stock Price', gridcolor=COLORS['grid'], color=COLORS['text']),
        showlegend=False,
        margin=dict(l=40, r=40, b=40, t=40)
    )
    
    return fig

def draw_payoff_diagram(engine, S, K, T, r, sigma, is_call, steps, american):
    """
    Creates a Payoff Diagram (Option Value vs Spot Price).
    """
    spots = np.linspace(S * 0.5, S * 1.5, 40)
    prices = []
    intrinsic = []
    
    for spot in spots:
        # --- COMPATIBILITY FIX ---
        # Both C++ and Python engines have 'calculate_option'
        # but only Python has 'binomial_price'. We use the common one.
        res = engine.calculate_option(spot, K, T, r, sigma, is_call, steps, american)
        prices.append(res.price) 
        
        iv = max(spot - K, 0) if is_call else max(K - spot, 0)
        intrinsic.append(iv)
        
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=spots, y=prices, name='Option Price',
        line=dict(color=COLORS['node_call'], width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=spots, y=intrinsic, name='Intrinsic Value',
        line=dict(color='grey', width=2, dash='dash')
    ))
    
    fig.add_vline(x=S, line_dash="dot", line_color="yellow", annotation_text="Current Spot")

    fig.update_layout(
        title={'text': "Option Payoff & Intrinsic Value", 'font': {'color': COLORS['text']}},
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['background'],
        xaxis=dict(title='Spot Price ($)', gridcolor=COLORS['grid'], color=COLORS['text']),
        yaxis=dict(title='Value ($)', gridcolor=COLORS['grid'], color=COLORS['text']),
        legend=dict(font=dict(color=COLORS['text'])),
        margin=dict(l=40, r=40, b=40, t=40)
    )
    
    return fig

def draw_greeks_chart(engine, S, K, T, r, sigma, is_call, steps, american):
    """
    Creates a chart showing Greeks (Delta, Gamma) sensitivity.
    """
    spots = np.linspace(S * 0.8, S * 1.2, 30)
    deltas = []
    gammas = []
    
    for spot in spots:
        res = engine.calculate_option(spot, K, T, r, sigma, is_call, steps, american)
        deltas.append(res.delta)
        gammas.append(res.gamma * 10) 
        
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=spots, y=deltas, name='Delta', line=dict(color='#ff9900', width=3)))
    fig.add_trace(go.Scatter(x=spots, y=gammas, name='Gamma (x10)', line=dict(color='#00ff88', width=3)))
    
    fig.update_layout(
        title={'text': "Greeks Sensitivity", 'font': {'color': COLORS['text']}},
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['background'],
        xaxis=dict(title='Spot Price ($)', gridcolor=COLORS['grid'], color=COLORS['text']),
        yaxis=dict(title='Greek Value', gridcolor=COLORS['grid'], color=COLORS['text']),
        legend=dict(font=dict(color=COLORS['text'])),
        margin=dict(l=40, r=40, b=40, t=40)
    )
    
    return fig