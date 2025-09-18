import os
import requests
import json
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import START, StateGraph, MessagesState, END
from langgraph.prebuilt import tools_condition, ToolNode
from operator import add
from typing import Annotated, TypedDict
from langchain_core.messages import HumanMessage, AIMessage

# Load environment variables from .env file
load_dotenv()

# Custom state to handle comprehensive financial data
class FinancialAnalysisState(TypedDict):
    messages: Annotated[list, add]
    ticker: str
    long_term_data: str
    short_term_data: str
    combined_data: str


def getFundamentalLongTermData(ticker: str) -> str:
    """Gets fundamental data for a given ticker from Financial Modeling Prep API

    Args:
        ticker: the ticker to get fundamental data for
    
    Returns:
        JSON string containing comprehensive financial data
    """
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return json.dumps({"error": "FMP_API_KEY not found in environment variables"})
    
    base_url = "https://financialmodelingprep.com/api/v3"
    
    try:
        # Get multiple financial datasets
        endpoints = {
            "income_statement": f"{base_url}/income-statement/{ticker}?limit=2&apikey={api_key}",
            "balance_sheet": f"{base_url}/balance-sheet-statement/{ticker}?limit=2&apikey={api_key}",
            "cash_flow": f"{base_url}/cash-flow-statement/{ticker}?limit=2&apikey={api_key}",
            "company_profile": f"{base_url}/profile/{ticker}?apikey={api_key}",
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
        
        # Add timestamp and ticker info
        fundamental_data["ticker"] = ticker.upper()
        fundamental_data["data_source"] = "Financial Modeling Prep"
        
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
        # Get quarterly financial datasets for last 2 quarters
        endpoints = {
            "quarterly_income_statement": f"{base_url}/income-statement/{ticker}?period=quarter&limit=2&apikey={api_key}",
            "quarterly_balance_sheet": f"{base_url}/balance-sheet-statement/{ticker}?period=quarter&limit=2&apikey={api_key}",
            "quarterly_cash_flow": f"{base_url}/cash-flow-statement/{ticker}?period=quarter&limit=2&apikey={api_key}",
            "quarterly_ratios": f"{base_url}/ratios/{ticker}?period=quarter&limit=2&apikey={api_key}",
            "quarterly_key_metrics": f"{base_url}/key-metrics/{ticker}?period=quarter&limit=2&apikey={api_key}",
            "quarterly_earnings": f"{base_url}/earnings/{ticker}?limit=2&apikey={api_key}",
            "quarterly_financial_growth": f"{base_url}/financial-growth/{ticker}?period=quarter&limit=2&apikey={api_key}",
            "company_profile": f"{base_url}/profile/{ticker}?apikey={api_key}"
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
        
        # Add metadata
        quarterly_data["ticker"] = ticker.upper()
        quarterly_data["data_source"] = "Financial Modeling Prep"
        quarterly_data["data_period"] = "Quarterly (Last 2 quarters)"
        
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


tools = [getFundamentalLongTermData, getFundamentalShortTermData]

# Define LLM with bound tools
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)

def extract_ticker(message: str) -> str:
    """Extract ticker symbol from user message"""
    import re
    # Look for ticker patterns (2-5 uppercase letters)
    ticker_pattern = r'\b[A-Z]{2,5}\b'
    matches = re.findall(ticker_pattern, message)
    
    # Filter out common non-ticker words and single letters
    exclude_words = {'THE', 'AND', 'OR', 'FOR', 'TO', 'FROM', 'WITH', 'BY', 'AT', 'IN', 'ON', 'IS', 'ARE', 'WAS', 'WERE', 'BE', 'BEEN', 'HAVE', 'HAS', 'HAD', 'DO', 'DOES', 'DID', 'WILL', 'WOULD', 'COULD', 'SHOULD', 'MAY', 'MIGHT', 'CAN', 'MUST', 'SHALL', 'GET', 'GOT', 'PUT', 'SET', 'LET', 'RUN', 'GO', 'SEE', 'SAY', 'SAID', 'TELL', 'TOLD', 'GIVE', 'GAVE', 'TAKE', 'TOOK', 'COME', 'CAME', 'WENT', 'WANT', 'KNOW', 'THINK', 'LOOK', 'USE', 'USED', 'WORK', 'MAKE', 'MADE', 'FIND', 'CALL', 'TRY', 'ASK', 'NEED', 'FEEL', 'SEEM', 'TURN', 'KEEP', 'SHOW', 'MOVE', 'PLAY', 'LIVE', 'HELP', 'TALK', 'BRING', 'HAPPEN', 'CARRY', 'SEND', 'BUILD', 'STAY', 'FALL', 'CUT', 'REACH', 'KILL', 'REMAIN', 'SUGGEST', 'RAISE', 'PASS', 'SELL', 'REQUIRE', 'REPORT', 'DECIDE', 'PULL', 'ME', 'MY', 'YOU', 'YOUR', 'ALL', 'BUT', 'NOT', 'OUT', 'SO', 'UP', 'NO', 'IF', 'NOW', 'WAY', 'WHO', 'OIL', 'NEW', 'TWO', 'HOW', 'ITS', 'OUR', 'HIS', 'HER', 'HIM', 'SHE', 'HE'}
    
    for match in matches:
        if match not in exclude_words and len(match) >= 2 and len(match) <= 5:
            return match
    
    # If no ticker found, return empty string
    return ""

def data_fetcher_node(state: FinancialAnalysisState) -> FinancialAnalysisState:
    """Fetch both long-term and short-term data simultaneously"""
    # Extract ticker from the latest user message
    latest_message = state["messages"][-1].content if state["messages"] else ""
    ticker = extract_ticker(latest_message)
    
    if not ticker:
        return {
            "messages": state["messages"],
            "ticker": "",
            "long_term_data": json.dumps({"error": "No valid ticker symbol found in message"}),
            "short_term_data": json.dumps({"error": "No valid ticker symbol found in message"}),
            "combined_data": json.dumps({"error": "No valid ticker symbol found in message"})
        }
    
    print(f"📊 Fetching data for ticker: {ticker}")
    print("⚡ Calling both long-term and short-term APIs simultaneously...")
    
    # Fetch both datasets simultaneously
    long_term_data = getFundamentalLongTermData(ticker)
    short_term_data = getFundamentalShortTermData(ticker)
    
    print(f"✅ Data fetching completed for {ticker}")
    
    return {
        "messages": state["messages"],
        "ticker": ticker,
        "long_term_data": long_term_data,
        "short_term_data": short_term_data,
        "combined_data": ""  # Will be populated by data_combiner_node
    }

def data_combiner_node(state: FinancialAnalysisState) -> FinancialAnalysisState:
    """Combine long-term and short-term data into a comprehensive dataset"""
    try:
        long_term = json.loads(state["long_term_data"])
        short_term = json.loads(state["short_term_data"])
        
        combined = {
            "ticker": state["ticker"],
            "analysis_type": "Comprehensive Financial Analysis",
            "data_sources": "Financial Modeling Prep",
            "long_term_analysis": {
                "description": "3-year historical annual data for trend analysis",
                "data": long_term
            },
            "short_term_analysis": {
                "description": "Last 2 quarters for recent performance analysis", 
                "data": short_term
            },
            "analyst_instructions": "Analyze both long-term trends and recent quarterly performance to provide comprehensive assessment"
        }
        
        return {"combined_data": json.dumps(combined, indent=2)}
        
    except Exception as e:
        error_data = {
            "error": f"Failed to combine data: {str(e)}",
            "ticker": state["ticker"]
        }
        return {"combined_data": json.dumps(error_data, indent=2)}

# System message
sys_msg = SystemMessage(content="""You are a professional equity research analyst specializing in fundamental analysis. 
You have been provided with comprehensive financial data including both long-term (3-year annual) and short-term (quarterly) data.

Your role is to analyze the provided comprehensive financial dataset to assess the stock's investment potential.

Your output must:
1. Provide a concise **summary** of the company's financial state based on both long-term trends and recent quarterly performance.
2. Assess **growth potential** (strong / moderate / weak) with justification from both historical trends and recent quarters.
3. Assess **risk factors** (low / moderate / high) with justification from financial ratios and trends.
4. Evaluate whether the stock appears **undervalued, fairly valued, or overvalued** relative to its sector and historical metrics.
5. Mention notable strengths and weaknesses (e.g., strong cash flow, high debt, sector trends, recent performance changes).
6. Output a **structured JSON object** with:
   - "growth_score" (0–10),
   - "risk_score" (0–10),
   - "valuation" ("undervalued" | "fairly_valued" | "overvalued"),
   - "summary" (3–5 sentence human-readable summary),
   - "notes" (key metrics and evidence in bullet points),
   - "long_term_trend" (analysis of 3-year trends),
   - "recent_performance" (analysis of last 2 quarters).

Keep your tone factual, objective, and professional. 
Base your analysis strictly on the provided comprehensive financial data.""")

def fundamentalAnalyst(state: FinancialAnalysisState) -> FinancialAnalysisState:
    """Analyze the combined financial data and provide investment recommendation"""
    # Create a message with the combined financial data
    analysis_prompt = f"""
    Please analyze the following comprehensive financial data for {state['ticker']}:
    
    {state['combined_data']}
    
    Provide your professional equity research analysis based on this data.
    """
    
    # Get analysis from LLM
    response = llm.invoke([sys_msg, HumanMessage(content=analysis_prompt)])
    
    return {"messages": [response]}

# Build graph with new structure
builder = StateGraph(FinancialAnalysisState)
builder.add_node("data_fetcher", data_fetcher_node)
builder.add_node("data_combiner", data_combiner_node) 
builder.add_node("fundamentalAnalyst", fundamentalAnalyst)

# Connect the nodes
builder.add_edge(START, "data_fetcher")
builder.add_edge("data_fetcher", "data_combiner")
builder.add_edge("data_combiner", "fundamentalAnalyst")
builder.add_edge("fundamentalAnalyst", END)

# Compile graph
graph = builder.compile()

def analyze_stock(message: str) -> dict:
    """
    Convenient wrapper function to analyze a stock with just a simple message
    
    Args:
        message: Simple message like "analyze AAPL" or "give me report on TSLA"
    
    Returns:
        Complete analysis result with ticker, data, and AI-generated summary
    
    Example:
        result = analyze_stock("analyze AAPL")
        print(f"Ticker: {result['ticker']}")
        print(f"Analysis: {result['messages'][-1].content}")
    """
    from langchain_core.messages import HumanMessage
    
    print(f"🎯 Starting analysis for: '{message}'")
    
    # Create the initial state from the simple message
    initial_state = {
        "messages": [HumanMessage(content=message)],
        "ticker": "",
        "long_term_data": "",
        "short_term_data": "",
        "combined_data": ""
    }
    
    # Run the graph with proper state
    result = graph.invoke(initial_state)
    
    print(f"🎉 Analysis completed for {result['ticker']}")
    return result
