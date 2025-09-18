import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import START, StateGraph, MessagesState
from utils.fundamental_analysis_tool import get_fundamental_data
from analyst_states import AnalystManagerState

# Load environment variables from .env file
load_dotenv()

# TODO: add tool for calling sector data for future comparisons


# Define LLM - no tools binding needed since we call getFundamentalData directly
model = ChatOpenAI(model="gpt-4o")



# System message
fundamental_analyst_sys_msg = SystemMessage(content="""You are a professional equity research analyst specializing in fundamental analysis.

    You have access to comprehensive financial data including:
    - 2 years of annual financial statements (income, balance sheet, cash flow)
    - 2 quarters of recent quarterly data (income, balance sheet, cash flow, earnings)
    - Financial ratios, key metrics, and enterprise values (both annual and quarterly)
    - Company profile (sector, industry, market cap, description)

    Your role is to analyze this comprehensive dataset to assess the stock's investment potential.

    Your output must:
    1. Provide a concise **summary** of the company's financial state based on both annual trends and recent quarterly performance.
    2. Assess **growth potential** (strong / moderate / weak) with justification from both historical and recent data.
    3. Assess **risk factors** (low / moderate / high) with justification from financial ratios and trends.
    4. Evaluate whether the stock appears **undervalued, fairly valued, or overvalued** 
       relative to its sector and key financial metrics.
    5. Mention notable strengths and weaknesses, highlighting any significant changes in recent quarters.
    6. Output a **structured JSON object** with:
       - "growth_score": {"score": 0-10, "justification": "brief explanation"},
       - "risk_score": {"score": 0-10, "justification": "brief explanation"},
       - "summary" (3–5 sentence human-readable summary),
       - "notes" (key metrics and evidence in bullet points),
       - "strengths_and_weaknesses": {"strengths": ["list of strengths"], "weaknesses": ["list of weaknesses"]}.

    Keep your tone factual, objective, and professional. 
    Base your analysis strictly on the comprehensive financial data provided.""")

# Node
def fundamental_analyst(state: AnalystManagerState) -> AnalystManagerState:
    """Analyze fundamental data and populate the fundamental_analysis state"""

    ticker = state["ticker"]
    # Get fundamental data
    fundamental_data = get_fundamental_data(ticker)
    
    # Create analysis request
    analysis_prompt = f"""
    Analyze the following fundamental data for {ticker} and provide your assessment:
    
    {fundamental_data}
    
    Please provide your analysis in the exact JSON format specified in the system message.
    """
    
    # Get analysis from LLM
    messages = [fundamental_analyst_sys_msg, HumanMessage(content=analysis_prompt)]
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
                "growth_score": {"score": 5, "justification": "Analysis failed to parse"},
                "risk_score": {"score": 5, "justification": "Analysis failed to parse"},
                "summary": "Failed to parse fundamental analysis",
                "notes": ["Parsing error occurred"],
                "strengths_and_weaknesses": {"strengths": [], "weaknesses": []}
            }
        
        # Populate fundamental_analysis state
        fundamental_analysis = {
            "summary": analysis_json.get("summary", ""),
            "growth_score": analysis_json.get("growth_score", {"score": 0, "justification": ""}),
            "risk_score": analysis_json.get("risk_score", {"score": 0, "justification": ""}),
            "notes": str(analysis_json.get("notes", "")),
            "strengths_and_weaknesses": analysis_json.get("strengths_and_weaknesses", {"strengths": [], "weaknesses": []})
        }
        
        return {"fundamental_analysis": fundamental_analysis}
        
    except (json.JSONDecodeError, AttributeError) as e:
        # Fallback if parsing fails
        fundamental_analysis = {
            "summary": f"Fundamental analysis completed for {ticker}",
            "growth_score": {"score": 5, "justification": "Analysis parsing failed"},
            "risk_score": {"score": 5, "justification": "Analysis parsing failed"},
            "notes": f"Error parsing analysis: {str(e)}",
            "strengths_and_weaknesses": {"strengths": [], "weaknesses": []}
        }
        
        return {"fundamental_analysis": fundamental_analysis}

# Build graph
builder = StateGraph(AnalystManagerState, input_schema=MessagesState)
builder.add_node("fundamentalAnalyst", fundamental_analyst)
builder.add_edge(START, "fundamentalAnalyst")

# Compile graph
graph = builder.compile()

# messages = graph.invoke({"messages": [HumanMessage(content="Analyze AAPL")]})


# for m in messages['messages']:
#     m.pretty_print()

