from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from utils.tavily_news_search_tool import tavily_news_search_tool



def news_analyst(state: MessagesState):
    """Analyze news data and provide market sentiment assessment for the ticker"""
    
    sys_msg = SystemMessage(content="""You are a professional news and sentiment analyst specializing in financial markets.
    
    You have access to a powerful news search tool that can fetch the latest news articles, press releases, 
    earnings reports, and market commentary for any stock ticker. Use the get_news_data tool to gather 
    comprehensive news information before performing your analysis.
    
    Your role is to analyze recent news articles and market commentary to assess:
    1. Overall market sentiment (Positive, Neutral, Negative)
    2. Key developments and catalysts that may impact stock performance
    3. Potential risks or opportunities identified in the news
    4. Market timing considerations based on recent events
    
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


llm = ChatOpenAI(model="gpt-4o")
tools = [tavily_news_search_tool]
llm_with_tools = llm.bind_tools(tools)

builder = StateGraph(MessagesState)
builder.add_node("news_analyst", news_analyst)
builder.add_node("news_analyst_manager", news_analyst_manager)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "news_analyst")
builder.add_conditional_edges(
    "news_analyst",
   tools_condition,
   path_map={"tools": "tools","__end__": "news_analyst_manager"}
)
builder.add_edge("tools", "news_analyst")
builder.add_edge("news_analyst_manager", END)
# Compile graph
graph = builder.compile()


