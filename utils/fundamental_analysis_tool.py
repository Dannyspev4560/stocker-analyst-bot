import os
import requests
import json
from dotenv import load_dotenv
from langchain_core.tools import tool

# Load environment variables from .env file
load_dotenv()


def getFundamentalLongTermData(ticker: str) -> str:
    """Gets yearly fundamental data for the last two years from Financial Modeling Prep API

    Args:
        ticker: the ticker to get fundamental data for
    
    Returns:
        JSON string containing yearly financial data for the last 2 years
    """
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return json.dumps({"error": "FMP_API_KEY not found in environment variables"})
    
    base_url = "https://financialmodelingprep.com/api/v3"
    
    try:
        # Get unique annual financial datasets (company_profile moved to getFundamentalData to avoid duplication)
        endpoints = {
            "income_statement": f"{base_url}/income-statement/{ticker}?limit=2&apikey={api_key}",
            "balance_sheet": f"{base_url}/balance-sheet-statement/{ticker}?limit=2&apikey={api_key}",
            "cash_flow": f"{base_url}/cash-flow-statement/{ticker}?limit=2&apikey={api_key}",
            "financial_ratios": f"{base_url}/ratios/{ticker}?limit=2&apikey={api_key}",
            "key_metrics": f"{base_url}/key-metrics/{ticker}?limit=2&apikey={api_key}",
            "enterprise_value": f"{base_url}/enterprise-values/{ticker}?limit=2&apikey={api_key}"
        }
        
        fundamental_data = {}
        
        for data_type, url in endpoints.items():
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:  # Check if data is not empty
                fundamental_data[data_type] = data
            else:
                fundamental_data[data_type] = f"No {data_type} data available for {ticker}"
        
        # Note: ticker and data_source metadata will be added by getFundamentalData
        
        return json.dumps(fundamental_data, indent=2)
        
    except requests.exceptions.RequestException as e:
        error_msg = {
            "error": f"API request failed: {str(e)}",
            "ticker": ticker,
            "data_source": "Financial Modeling Prep"
        }
        return json.dumps(error_msg, indent=2)
    
    except json.JSONDecodeError as e:
        error_msg = {
            "error": f"Failed to parse API response: {str(e)}",
            "ticker": ticker,
            "data_source": "Financial Modeling Prep"
        }
        return json.dumps(error_msg, indent=2)
    
    except Exception as e:
        error_msg = {
            "error": f"Unexpected error: {str(e)}",
            "ticker": ticker,
            "data_source": "Financial Modeling Prep"
        }
        return json.dumps(error_msg, indent=2)

def getFundamentalShortTermData(ticker: str) -> str:
    """Gets quarterly fundamental data for the last two quarters from Financial Modeling Prep API

    Args:
        ticker: the ticker to get quarterly fundamental data for
    
    Returns:
        JSON string containing quarterly financial data for the last 2 quarters
    """
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return json.dumps({"error": "FMP_API_KEY not found in environment variables"})
    
    base_url = "https://financialmodelingprep.com/api/v3"
    
    try:
        # Get unique quarterly financial datasets (company_profile moved to getFundamentalData to avoid duplication)
        endpoints = {
            "quarterly_income_statement": f"{base_url}/income-statement/{ticker}?period=quarter&limit=2&apikey={api_key}",
            "quarterly_balance_sheet": f"{base_url}/balance-sheet-statement/{ticker}?period=quarter&limit=2&apikey={api_key}",
            "quarterly_cash_flow": f"{base_url}/cash-flow-statement/{ticker}?period=quarter&limit=2&apikey={api_key}",
            "quarterly_ratios": f"{base_url}/ratios/{ticker}?period=quarter&limit=2&apikey={api_key}",
            "quarterly_key_metrics": f"{base_url}/key-metrics/{ticker}?period=quarter&limit=2&apikey={api_key}",
            "quarterly_earnings": f"{base_url}/earnings/{ticker}?limit=2&apikey={api_key}",
            "quarterly_financial_growth": f"{base_url}/financial-growth/{ticker}?period=quarter&limit=2&apikey={api_key}"
        }
        
        quarterly_data = {}
        
        for data_type, url in endpoints.items():
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:  # Check if data is not empty
                quarterly_data[data_type] = data
            else:
                quarterly_data[data_type] = f"No {data_type} data available for {ticker}"
        
        # Note: ticker and data_source metadata will be added by getFundamentalData
        
        return json.dumps(quarterly_data, indent=2)
        
    except requests.exceptions.RequestException as e:
        error_msg = {
            "error": f"API request failed: {str(e)}",
            "ticker": ticker,
            "data_source": "Financial Modeling Prep",
            "data_period": "Quarterly"
        }
        return json.dumps(error_msg, indent=2)
    
    except json.JSONDecodeError as e:
        error_msg = {
            "error": f"Failed to parse API response: {str(e)}",
            "ticker": ticker,
            "data_source": "Financial Modeling Prep",
            "data_period": "Quarterly"
        }
        return json.dumps(error_msg, indent=2)
    
    except Exception as e:
        error_msg = {
            "error": f"Unexpected error: {str(e)}",
            "ticker": ticker,
            "data_source": "Financial Modeling Prep",
            "data_period": "Quarterly"
        }
        return json.dumps(error_msg, indent=2)




@tool   
def get_fundamental_data(ticker: str) -> str:
    """Gets both yearly and quarterly fundamental data for the last two years and two quarters from Financial Modeling Prep API
    
    This function combines unique data from both long-term and short-term functions. 
    Company profile data is handled separately by the get_company_profile tool.
    
    Args:
        ticker: the ticker to get fundamental data for
    
    Returns:
        JSON string containing comprehensive financial data (yearly + quarterly data only)
    """
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return json.dumps({"error": "FMP_API_KEY not found in environment variables"})
    
    base_url = "https://financialmodelingprep.com/api/v3"
    
    

    try:
        combined_data = {}
        
        # Get unique long-term data
        long_term_data = getFundamentalLongTermData(ticker)
        long_term_json = json.loads(long_term_data)
        
        # Get unique short-term data  
        short_term_data = getFundamentalShortTermData(ticker)
        short_term_json = json.loads(short_term_data)
        
        # Combine all data
        if "error" not in long_term_json:
            combined_data.update(long_term_json)
        
        if "error" not in short_term_json:
            combined_data.update(short_term_json)
        
        # Add metadata
        combined_data["ticker"] = ticker.upper()
        combined_data["data_source"] = "Financial Modeling Prep"
        combined_data["data_type"] = "Comprehensive (Annual + Quarterly)"
        
        return json.dumps(combined_data, indent=2)
        
    except requests.exceptions.RequestException as e:
        error_msg = {
            "error": f"API request failed: {str(e)}",
            "ticker": ticker,
            "data_source": "Financial Modeling Prep"
        }
        return json.dumps(error_msg, indent=2)
    
    except json.JSONDecodeError as e:
        error_msg = {
            "error": f"Failed to parse API response: {str(e)}",
            "ticker": ticker,
            "data_source": "Financial Modeling Prep"
        }
        return json.dumps(error_msg, indent=2)
    
    except Exception as e:
        error_msg = {
            "error": f"Unexpected error: {str(e)}",
            "ticker": ticker,
            "data_source": "Financial Modeling Prep"
        }
        return json.dumps(error_msg, indent=2)