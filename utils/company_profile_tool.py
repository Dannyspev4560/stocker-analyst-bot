import os
import requests
import json
from dotenv import load_dotenv
from langchain_core.tools import tool
from analyst_states import AnalystManagerState


# Load environment variables from .env file
load_dotenv()



def get_company_profile(state: AnalystManagerState) -> AnalystManagerState:
    """Gets company profile information from Financial Modeling Prep API
    
    Fetches comprehensive company information including sector, industry, market cap, 
    business description, and key company details.
    
    Args:
        state: AnalystManagerState containing the ticker to analyze
    
    Returns:
        AnalystManagerState with company_profile populated
    """
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        error_data = {
            "error": "FMP_API_KEY not found in environment variables"
        }
        state.company_profile = json.dumps(error_data, indent=2)
        return state
    
    base_url = "https://financialmodelingprep.com/api/v3"
    ticker = state.get("ticker", "")
    # Validate ticker parameter
    if not ticker:
        error_data = {
            "error": "No ticker provided"
        }
        return {"company_profile": json.dumps(error_data, indent=2)}
    try:
        # Company profile endpoint
        url = f"{base_url}/profile/{ticker}?apikey={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data:
            # Return company profile data
            profile_data = {
                "company_profile": data,
            }
            return {"company_profile": json.dumps(profile_data, indent=2)}
        else:
            # Return error information
            error_data = {
                "error": f"No company profile data available for {ticker}"
            }
            state.company_profile = json.dumps(error_data, indent=2)
            return state
        
    except requests.exceptions.RequestException as e:
        error_data = {
            "error": f"API request failed: {str(e)}"
        }
        state.company_profile = json.dumps(error_data, indent=2)
        return state
    
    except json.JSONDecodeError as e:
        error_data = {
            "error": f"Failed to parse API response: {str(e)}"
        }
        state.company_profile = json.dumps(error_data, indent=2)
        return state
    
    except Exception as e:
        error_data = {
            "error": f"Unexpected error: {str(e)}"
        }
        state.company_profile = json.dumps(error_data, indent=2)
        return state
