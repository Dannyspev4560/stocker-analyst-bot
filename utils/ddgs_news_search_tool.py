from duckduckgo_search import DDGS
from datetime import datetime
import json

def parse_duckduckgo_date(date_str):
    """
    Parse DuckDuckGo date string to datetime.
    DuckDuckGo may return formats like:
    - '2025-09-30T15:20:00Z'
    - '30 Sep 2025'
    - None
    """
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%d %b %Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def get_duckduckgo_news(query, start_date, end_date, max_results=50, region="us-en"):
    """
    Fetch DuckDuckGo news for a query within a date range.
    Returns JSON.
    """
    # Convert input dates to datetime
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    results = []
    with DDGS() as ddgs:
        for r in ddgs.news(query, region=region, max_results=max_results):
            news_date = parse_duckduckgo_date(r.get("date"))

            # Only keep results within the date range
            if news_date and start_dt <= news_date <= end_dt:
                results.append({
                    "title": r.get("title"),
                    "date": news_date.strftime("%Y-%m-%d") if news_date else None,
                    "source": r.get("source"),
                    "link": r.get("url"),
                    "snippet": r.get("body")
                })

    return json.dumps(results, indent=2, ensure_ascii=False)


# Example usage
if __name__ == "__main__":
    news_json = get_duckduckgo_news("AAPL stock", start_date="2025-09-01", end_date="2025-09-30", max_results=50)
    
    # Save to file
    with open("duckduckgo_news_filtered.json", "w", encoding="utf-8") as f:
        f.write(news_json)

    print("✅ Saved duckduckgo_news_filtered.json")
    print(news_json[:500])  # show first results