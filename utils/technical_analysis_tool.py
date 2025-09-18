import pandas as pd
import numpy as np
import json
import requests
from datetime import datetime, timedelta
from stockstats import wrap
from dotenv import load_dotenv
from langchain_core.tools import tool
import os
import tempfile
import sys

# Load environment variables from .env file
load_dotenv()

@tool
def get_technical_analysis(ticker: str) -> str:
    """Get technical analysis data for a stock ticker.
    
    Args:
        ticker: The stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'TSLA')
        
    Returns:
        JSON string with technical indicators, price data, and market analysis for the last 3 months
    """
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return json.dumps({"error": "FMP_API_KEY not found in environment variables"})
    
    base_url = "https://financialmodelingprep.com/api/v3"
    
    try:
        # Calculate date range for last 3 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # Approximately 3 months
        
        # Format dates for API call
        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')
        
        # FMP historical price endpoint
        url = f"{base_url}/historical-price-full/{ticker}?from={from_date}&to={to_date}&apikey={api_key}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        api_data = response.json()
        
        if not api_data or 'historical' not in api_data:
            return json.dumps({"error": f"No historical data available for {ticker}"})
        
        # Process and format the data
        data = []
        historical_data = api_data['historical']
        
        # Sort by date (oldest first) for technical analysis
        historical_data.sort(key=lambda x: x['date'])
        
        for day_data in historical_data:
            date = datetime.strptime(day_data['date'], '%Y-%m-%d')
            
            data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Open': round(day_data['open'], 2),
                'High': round(day_data['high'], 2),
                'Low': round(day_data['low'], 2),
                'Close': round(day_data['close'], 2),
                'Volume': int(day_data['volume'])
            })
        
        # Convert to DataFrame for technical analysis
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        # Rename columns for stockstats (it expects lowercase)
        df.columns = [col.lower() for col in df.columns]
        
        # Apply technical indicators using stockstats
        stock_df = wrap(df)
        
        # Calculate technical indicators
        try:
            # Force calculation of indicators
            sma_20 = stock_df['close_20_sma'].iloc[-1] if len(df) >= 20 else None
            sma_50 = stock_df['close_50_sma'].iloc[-1] if len(df) >= 50 else None
            rsi_14 = stock_df['rsi_14'].iloc[-1] if len(df) >= 14 else None
            macd = stock_df['macd'].iloc[-1] if len(df) >= 26 else None
            boll_ub = stock_df['boll_ub'].iloc[-1] if len(df) >= 20 else None
            boll_lb = stock_df['boll_lb'].iloc[-1] if len(df) >= 20 else None
        except (KeyError, IndexError):
            sma_20 = sma_50 = rsi_14 = macd = boll_ub = boll_lb = None
        
        # TODO: add more technical indicators 
        # Removed raw data from the returned object to save tokens and keep the object concise

        # Add common technical indicators
        technical_data = {
            "ticker": ticker.upper(),
            "data_period": f"{from_date} to {to_date}",
            "total_days": len(data),
            "latest_data":{
                "date": data[-1]['Date'],
                "open": data[-1]['Open'],
                "high": data[-1]['High'],
                "low": data[-1]['Low'],
                "close": data[-1]['Close'],
                "volume": data[-1]['Volume']
            },
            "technical_indicators": {
                "sma_20": round(float(sma_20), 2) if sma_20 and not pd.isna(sma_20) else None,
                "sma_50": round(float(sma_50), 2) if sma_50 and not pd.isna(sma_50) else None,
                "rsi_14": round(float(rsi_14), 2) if rsi_14 and not pd.isna(rsi_14) else None,
                "macd": round(float(macd), 4) if macd and not pd.isna(macd) else None,
                "bollinger_upper": round(float(boll_ub), 2) if boll_ub and not pd.isna(boll_ub) else None,
                "bollinger_lower": round(float(boll_lb), 2) if boll_lb and not pd.isna(boll_lb) else None,
                "price_change_3m": round(((data[-1]['Close'] - data[0]['Close']) / data[0]['Close']) * 100, 2),
                "avg_volume": round(sum([d['Volume'] for d in data]) / len(data)),
                "volatility_3m": round(df['close'].std(), 2)
            }
        }
        
        return json.dumps(technical_data, indent=2, default=str)
        
    except requests.exceptions.RequestException as e:
        error_msg = {
            "error": f"API request failed: {str(e)}",
            "ticker": ticker,
            "data_source": "Financial Modeling Prep"
        }
        return json.dumps(error_msg, indent=2)
    
    except Exception as e:
        error_msg = {
            "error": f"Technical analysis failed: {str(e)}",
            "ticker": ticker,
            "data_source": "Financial Modeling Prep"
        }
        return json.dumps(error_msg, indent=2)

def test_technical_analysis():
    """Test function to verify technical analysis works with AMZN"""
    print("🧪 Testing technical analysis with AMZN...")
    
    result = get_technical_analysis("AMZN")
    data = json.loads(result)
    
    if 'error' in data:
        print(f"❌ Error: {data['error']}")
        return False
    
    print("✅ Technical analysis successful!")
    print(f"📊 Ticker: {data.get('ticker', 'N/A')}")
    print(f"📅 Data period: {data.get('data_period', 'N/A')}")
    print(f"📈 Total days: {data.get('total_days', 0)}")
    
    tech_indicators = data.get('technical_indicators', {})
    print(f"💹 Current price: ${tech_indicators.get('current_price', 'N/A')}")
    print(f"📊 3-month change: {tech_indicators.get('price_change_3m', 'N/A')}%")
    print(f"📈 SMA 20: ${tech_indicators.get('sma_20', 'N/A')}")
    print(f"🔄 RSI 14: {tech_indicators.get('rsi_14', 'N/A')}")
    print(f"📊 Volatility: {tech_indicators.get('volatility_3m', 'N/A')}")
    
    return True

if __name__ == "__main__":
    test_technical_analysis()

