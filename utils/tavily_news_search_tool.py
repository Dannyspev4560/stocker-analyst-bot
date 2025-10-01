from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool


@tool
def tavily_news_search_tool(ticker: str) -> str:
    """Gets the latest news and market sentiment data for a given stock ticker.
    
    Uses Tavily search to fetch recent news articles, press releases, and market commentary
    related to the specified stock ticker. This provides crucial context for understanding
    recent developments, earnings reports, analyst opinions, and market sentiment that may
    impact the stock's performance.
    
    Args:
        ticker: The stock ticker symbol to search for news (e.g., "AAPL", "TSLA", "GOOGL")
    
    Returns:
        JSON string containing recent news articles with titles, snippets, URLs, and publication dates
        that can be analyzed for market sentiment and potential impact on stock performance
    """
    try:
        search = TavilySearchResults(max_results=5)
        
        # Search for comprehensive news about the ticker
        search_query = f"{ticker} stock news earnings analyst reports latest developments"
        news_results = search.invoke(search_query)
        
        # Structure the results for better analysis
        news_data = {
            "articles": news_results,
            "article_count": len(news_results) if news_results else 0
        }
        
        return news_data
        
    except Exception as e:
        error_data = {
            "error": f"Failed to fetch news data: {str(e)}",
            "articles": []
        }
        return error_data