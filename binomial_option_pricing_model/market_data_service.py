import yfinance as yf
import numpy as np
import pandas as pd

def fetch_stock_data(ticker_symbol):
    """
    Fetches real-time stock data and calculates volatility for a given ticker.

    How it works:
    1.  **API**: Uses `yfinance`, which connects to Yahoo Finance's public API.
        -   URL (Internal): `https://query2.finance.yahoo.com/v8/finance/chart/{ticker}`
    2.  **Data Received**: We get a JSON-like structure containing timestamps and OHLC (Open, High, Low, Close) prices.

    Args:
        ticker_symbol (str): The stock symbol (e.g., 'AAPL', 'GOOGL', 'MSFT').

    Returns:
        dict: A dictionary containing:
            - 'price' (float): The most recent trading price.
            - 'volatility' (float): Annualized volatility calculated from 1-month history.
            - 'error' (str): Error message if something goes wrong, else None.
    """
    try:
        # Step 1: Initialize the Ticker object
        # This doesn't fetch data yet, just preps the object.
        stock = yf.Ticker(ticker_symbol)

        # Step 2: Fetch Current Price
        # We use 'fast_info' which is optimized for just getting the latest price.
        # It's faster than the standard .info dictionary.
        try:
            current_price = stock.fast_info['last_price']
        except:
            # Fallback to standard history if fast_info fails
            hist_today = stock.history(period="1d")
            if hist_today.empty:
                return {'error': f"Could not find price for {ticker_symbol}"}
            current_price = hist_today['Close'].iloc[-1]

        # Step 3: Calculate Volatility
        # We need historical data to measure how much the price moves.
        # We fetch 1 month of daily data.
        hist = stock.history(period="1mo")
        
        if hist.empty:
             return {'error': f"No historical data found for {ticker_symbol}"}

        # Calculate daily returns: ln(Price_today / Price_yesterday)
        # We use Log Returns because they are time-additive and commonly used in finance.
        hist['Returns'] = np.log(hist['Close'] / hist['Close'].shift(1))
        
        # Calculate Standard Deviation of these returns
        # This gives us "Daily Volatility"
        daily_volatility = hist['Returns'].std()
        
        # Annualize it
        # There are approx 252 trading days in a year.
        # Annual Volatility = Daily Vol * Sqrt(252)
        annualized_volatility = daily_volatility * np.sqrt(252)

        # Return the clean data
        return {
            'price': round(float(current_price), 2),
            'volatility': round(float(annualized_volatility), 2), # e.g., 0.25 for 25%
            'error': None
        }

    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    # Test the function directly when running this file
    print("--- Testing Market Data Service ---")
    ticker = "AAPL"
    print(f"Fetching data for {ticker}...")
    data = fetch_stock_data(ticker)
    print(f"Result: {data}")
