import re
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import END, START, StateGraph, MessagesState
from analysts.analyst_manager import analyst_manager
from analysts.fundamental_agent import fundamental_analyst
from analysts.technical_analyst import technical_analyst
from analyst_states import AnalystManagerState
from utils.company_profile_tool import get_company_profile

# Load environment variables from .env file
load_dotenv()

llm = ChatOpenAI(model="gpt-4o")
small_llm = ChatOpenAI(model="gpt-4o-mini")

def ticker_extractor(state: MessagesState) -> AnalystManagerState:
    """Extract ticker from the input message string"""
    
    # System message for ticker extraction
    ticker_extraction_msg = SystemMessage(content="""You are a ticker extraction specialist. 
    Your job is to extract the stock ticker symbol from user messages.
    
    Rules:
    - Look for 2-5 letter uppercase stock symbols (e.g., AAPL, TSLA, GOOGL, MSFT)
    - The ticker might be in phrases like "analyze AAPL", "TSLA stock", "look at GOOGL"
    - Only return the ticker symbol itself, nothing else
    - If you can't find a clear ticker, return "UNKNOWN"
    
    Examples:
    - "analyze AAPL" → AAPL
    - "I want to know about Tesla stock TSLA" → TSLA  
    - "Can you analyze GOOGL for me?" → GOOGL
    - "What about MSFT?" → MSFT
    """)

    response = llm.invoke([ticker_extraction_msg] + state["messages"])
    ticker = response.content

    if not re.match(r"^[A-Z]{2,5}$", ticker):
        ticker = ""
    
    return {
            "messages": [response],
            "ticker": ticker
           }


def ticker_condition(state: AnalystManagerState) -> str:
        return "has_ticker" if state["ticker"] else "no_ticker"


builder = StateGraph(AnalystManagerState, input_schema=MessagesState)

builder.add_node("ticker_extractor", ticker_extractor)
builder.add_node("get_company_profile", get_company_profile)

builder.add_node("fundamental_analyst", fundamental_analyst)
builder.add_node("technical_analyst", technical_analyst)
builder.add_node("analyst_manager", analyst_manager)

# Start with state initialization to extract ticker
builder.add_edge(START, "ticker_extractor")

builder.add_conditional_edges("ticker_extractor", ticker_condition, path_map={"has_ticker": "get_company_profile", "no_ticker": END})
# Then run fundamental analyst and technical analyst parallelly
builder.add_edge("get_company_profile", "fundamental_analyst")
builder.add_edge("get_company_profile", "technical_analyst")
# Finally, combine results in analyst manager
builder.add_edge("fundamental_analyst", "analyst_manager")
builder.add_edge("technical_analyst", "analyst_manager")
builder.add_edge("analyst_manager", END)

graph = builder.compile()