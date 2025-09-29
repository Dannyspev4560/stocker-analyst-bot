import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import START, StateGraph, MessagesState
from analyst_states import AnalystManagerState
from utils.technical_analysis_tool import get_technical_analysis



sys_msg = SystemMessage(content="""You are a professional technical analyst specializing in stock market technical analysis.

You have access to a technical analysis tool that provides:
- 3 months of daily market data (OHLCV) for any stock ticker
- Key technical indicators: SMA 20/50, RSI 14, MACD, Bollinger Bands
- Price performance metrics: 3-month change, volatility, average volume
- Latest market data: current price, recent OHLC data

Your role is to analyze the technical indicators and market data to provide trading recommendations.

Your analysis process:
1. Use the technical analysis tool to get comprehensive market data for the requested ticker
2. Evaluate the technical indicators:
   - Moving Averages: Price position relative to SMA 20/50 (trend direction)
   - RSI: Oversold (<30) or Overbought (>70) conditions
   - MACD: Momentum and trend changes
   - Bollinger Bands: Volatility and potential breakouts
   - Volume: Confirmation of price moves
3. Consider overall market momentum and volatility

Your output must be a **structured JSON object** with:
- "recommendation": "BUY" | "HOLD" | "SELL" | "NONE"
- "confidence": "HIGH" | "MEDIUM" | "LOW"
- "summary": "2-3 sentence explanation of your recommendation based on technical indicators"
- "key_indicators": ["list of 3-4 most important technical signals supporting your decision"]
- "price_target": "potential target price or range if applicable, null otherwise"
- "risk_level": "LOW" | "MEDIUM" | "HIGH"

Recommendation guidelines:
- BUY: Strong bullish signals, upward momentum, good entry point
- SELL: Strong bearish signals, downward momentum, risk of further decline  
- HOLD: Mixed signals, sideways trend, wait for clearer direction
- NONE: Insufficient data or highly volatile/uncertain conditions

Keep your analysis objective and based strictly on technical indicators. Do not speculate beyond the provided data.""")


# Define LLM - no tools binding needed since we call get_technical_analysis directly
model = ChatOpenAI(model="gpt-4o")


def technical_analyst(state: AnalystManagerState) -> AnalystManagerState:
    # Get technical data directly
    ticker = state["ticker"]
    technical_data = get_technical_analysis(ticker)
    
    # Create analysis request
    analysis_prompt = f"""
    Analyze the following technical data for {ticker} and provide your trading recommendation:
    
    {technical_data}
    
    Please provide your analysis in the exact JSON format specified in the system message.
    """
    
    # Get analysis from LLM
    messages = [sys_msg, HumanMessage(content=analysis_prompt)]
    response = model.invoke(messages)
    
    # Parse the response to extract the structured data
    try:
        # Extract JSON from the response content
        response_content = response.content
        # Try to find JSON in the response
        import re
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            analysis_json = json.loads(json_match.group())
        else:
            # Fallback if JSON parsing fails
            analysis_json = {
                "recommendation": "NONE",
                "confidence": "LOW",
                "summary": "Failed to parse technical analysis",
                "key_indicators": ["Parsing error occurred"],
                "price_target": None,
                "risk_level": "HIGH"
            }
        
        # Populate technical_analysis state
        technical_analysis = {
            "recommendation": analysis_json.get("recommendation", "NONE"),
            "confidence": analysis_json.get("confidence", "LOW"),
            "summary": analysis_json.get("summary", ""),
            "key_indicators": analysis_json.get("key_indicators", []),
            "price_target": analysis_json.get("price_target", ""),
            "risk_level": analysis_json.get("risk_level", "MEDIUM")
        }
        
        return {"technical_analysis": technical_analysis}
        
    except (json.JSONDecodeError, AttributeError) as e:
        # Fallback if parsing fails
        technical_analysis = {
            "recommendation": "NONE",
            "confidence": "LOW", 
            "summary": f"Technical analysis completed for {ticker}",
            "key_indicators": [f"Error parsing analysis: {str(e)}"],
            "price_target": "",
            "risk_level": "HIGH"
        }
        
        return {"technical_analysis": technical_analysis}

# Build graph
builder = StateGraph(AnalystManagerState)
builder.add_node("technical_analyst", technical_analyst)
builder.add_edge(START, "technical_analyst")

# Compile graph
graph = builder.compile()