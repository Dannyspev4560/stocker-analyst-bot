from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from utils.google_news_search_tool import google_news_search_tool
from utils.tavily_news_search_tool import tavily_news_search_tool



def news_analyst(state: MessagesState):
    """Analyze news data and provide market sentiment assessment for the ticker"""
    
    sys_msg = SystemMessage(content="""You are a professional news and sentiment analyst specializing in financial markets.
    
    You have access to multiple news search tools with a fallback strategy to ensure reliable data retrieval:
    
    1. **Primary Tool - Google News Search**: Use this first to fetch the latest news articles, press releases, 
       earnings reports, and market commentary. This tool provides comprehensive web scraping of full article content.
    
    2. **Fallback Tool - Tavily Search**: If the Google search fails or returns insufficient results, 
       use this as a backup to gather news information with reliable API-based search.
    
    **Search Strategy**: Always try the Google search tool first. If it encounters errors, timeouts, or returns 
    no useful results, then use the Tavily search tool as a reliable fallback to ensure you always have 
    news data for your analysis.
    
    Your role is to analyze recent news articles and market commentary to assess:
    1. Overall market sentiment (Positive, Neutral, Negative)
    2. Key developments and catalysts that may impact stock performance
    3. Potential risks or opportunities identified in the news
    4. Market timing considerations based on recent events
    5. Base your analysis on the most recent news articles and market commentary - prefer the most recent ones
    
    **Process**:
    1. First, attempt to use the Google News search tool to gather comprehensive news data
    2. If Google search fails, encounters errors, or returns insufficient results, use the Tavily search tool as backup
    3. Analyze the retrieved news articles and extract key insights
    4. Provide your assessment in the structured JSON format below
    
    Provide your analysis in structured JSON format:
    {
        "sentiment": "Positive" | "Neutral" | "Negative",
        "confidence": "High" | "Medium" | "Low",
        "key_developments": ["list of important news items"],
        "potential_catalysts": ["upcoming events or developments"],
        "risks": ["identified risk factors from news"],
        "summary": "2-3 sentence summary of news impact on stock"
    }
    """)
    

    response = llm_with_tools.invoke([sys_msg] + state["messages"])

    return {"messages": [response]}


def news_analyst_manager(state: MessagesState):
    sys_msg = SystemMessage(content="""You are a news analyst manager.
    you are given an analysis of the news about a stock ticker and based on that analysis, you need to provide a summary of the news and the impact on the stock.
    provider your analysis in a JSON format with the following fields:
    {
        "summary": "2-3 sentence summary of news impact on stock"
    }
    """)

    response = llm_with_tools.invoke([sys_msg] + state["messages"])

    return {"messages": [response]}

def news_analyst_condition(state: MessagesState) -> str:
    route = tools_condition(state)
    if route == "tools":
        return "tools"
    return "default"


llm = ChatOpenAI(model="gpt-4o")
tools = [google_news_search_tool, tavily_news_search_tool]
llm_with_tools = llm.bind_tools(tools)

builder = StateGraph(MessagesState)
builder.add_node("news_analyst", news_analyst)
builder.add_node("news_analyst_manager", news_analyst_manager)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "news_analyst")
builder.add_conditional_edges(
    "news_analyst",
   news_analyst_condition,
   path_map={"tools": "tools","default": "news_analyst_manager"}
)
builder.add_edge("tools", "news_analyst")
builder.add_edge("news_analyst_manager", END)
# Compile graph
graph = builder.compile()


