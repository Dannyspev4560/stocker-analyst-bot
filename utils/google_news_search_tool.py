from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import time

def make_request(url, headers, retries=3, delay=2):
    """Helper function to make HTTP requests with retries."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Request failed (attempt {attempt+1}): {e}")
            time.sleep(delay)
    raise Exception("Failed after multiple retries")


@tool
def google_news_search_tool(ticker: str, start_date: str, end_date: str, max_pages: int = 2):
    """
    Scrape Google News search results for a given query and date range.
    Returns results in JSON format.

    Args:
        query: The search query to use
        start_date: The start date to use
        end_date: The end date to use
        max_pages: The maximum number of pages to scrape

    Returns:
        JSON string containing the search results
    """
    # Convert ISO date (yyyy-mm-dd) to Google format (mm/dd/yyyy)
    if "-" in start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%m/%d/%Y")
    if "-" in end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m/%d/%Y")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/101.0.4951.54 Safari/537.36"
        )
    }

    news_results = []
    page = 0

    query = f"{ticker} stock"

    while page < max_pages:  # limit pages to avoid IP block
        offset = page * 10
        url = (
            f"https://www.google.com/search?q={query}"
            f"&tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}"
            f"&tbm=nws&hl=en&gl=us&start={offset}"
        )

        try:
            response = make_request(url, headers)
            soup = BeautifulSoup(response.content, "html.parser")
            results_on_page = soup.select("div.SoaBEf")

            if not results_on_page:
                break  # No more results found

            for el in results_on_page:
                try:
                    link = el.find("a")["href"]
                    title = el.select_one("div.MBeuO").get_text()
                    snippet = el.select_one(".GI74Re").get_text()
                    date = el.select_one(".LfVVr").get_text()
                    source = el.select_one(".NUnG9d span").get_text()
                    news_results.append(
                        {
                            "link": link,
                            "title": title,
                            "snippet": snippet,
                            "date": date,
                            "source": source,
                        }
                    )
                except Exception as e:
                    print(f"Error processing result: {e}")
                    continue

            # Check for "Next" page
            next_link = soup.find("a", id="pnnext")
            if not next_link:
                break

            page += 1
            time.sleep(1)  # be polite, avoid fast scraping :) 

        except Exception as e:
            print(f"Failed after multiple retries: {e}")
            break

    return json.dumps(news_results, indent=2, ensure_ascii=False)


# Example usage
if __name__ == "__main__":
    results_json = google_news_search_tool("ORCL", "2025-09-01", "2025-09-30")

    # Save to file
    with open("news_results.json", "w", encoding="utf-8") as f:
        f.write(results_json)

    print("✅ Saved news_results.json")
    print(results_json[:500])  # print first part

