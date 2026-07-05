"""
Web Search Tool for StudyMate AI Agents

Provides web search capabilities using SerpAPI (Google Search).
Agents can use this to find latest documentation, tutorials, and resources.
"""

import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def web_search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web using SerpAPI (Google Search).
    
    Args:
        query: Search query string
        num_results: Number of results to return (default: 5)
    
    Returns:
        List of dictionaries with 'title', 'link', 'snippet'
    
    Example:
        results = web_search("Azure Functions Python tutorial")
        for result in results:
            print(f"{result['title']}: {result['link']}")
    """
    
    if not SERPAPI_KEY:
        return [{
            "title": "Search Unavailable",
            "link": "https://serpapi.com",
            "snippet": "Please add SERPAPI_KEY to your .env file to enable web search. Get free API key at https://serpapi.com"
        }]
    
    try:
        # SerpAPI endpoint
        url = "https://serpapi.com/search"
        
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": num_results,
            "engine": "google"
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract organic results
        results = []
        for item in data.get("organic_results", [])[:num_results]:
            results.append({
                "title": item.get("title", "No title"),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "No description available")
            })
        
        # print(f"DEBUG: Got {len(results)} results")  # useful for debugging search issues
        return results if results else [{
            "title": "No results found",
            "link": "",
            "snippet": f"No search results found for: {query}"
        }]
        
    except requests.exceptions.RequestException as e:
        return [{
            "title": "Search Error",
            "link": "",
            "snippet": f"Error performing search: {str(e)}"
        }]
    except Exception as e:
        return [{
            "title": "Search Error",
            "link": "",
            "snippet": f"Unexpected error: {str(e)}"
        }]


def search_documentation(topic: str, platform: str = "microsoft", num_results: int = 3) -> List[Dict[str, str]]:
    """
    Search for official documentation on specific platforms.
    
    Args:
        topic: What to search for (e.g., "Azure Functions triggers")
        platform: Platform to search (default: "microsoft")
        num_results: Number of results (default: 3)
    
    Returns:
        List of documentation links with titles and snippets
    
    Example:
        docs = search_documentation("API authentication", "microsoft")
    """
    
    # Platform-specific search queries
    platform_domains = {
        "microsoft": "site:learn.microsoft.com OR site:docs.microsoft.com",
        "azure": "site:learn.microsoft.com/azure OR site:azure.microsoft.com",
        "python": "site:docs.python.org",
        "github": "site:docs.github.com"
    }
    
    domain = platform_domains.get(platform.lower(), "site:learn.microsoft.com")
    query = f"{topic} {domain}"
    
    return web_search(query, num_results)


def format_search_results(results: List[Dict[str, str]], max_results: int = 3) -> str:
    """
    Format search results into a readable string for agent consumption.
    
    Args:
        results: List of search result dictionaries
        max_results: Maximum number of results to format
    
    Returns:
        Formatted string with search results
    """
    if not results:
        return "No search results available."
    
    formatted = "[SEARCH RESULTS]\n\n"
    
    for i, result in enumerate(results[:max_results], 1):
        formatted += f"{i}. {result['title']}\n"
        formatted += f"   Link: {result['link']}\n"
        formatted += f"   {result['snippet']}\n\n"
    
    return formatted


# Tool metadata for agent integration
TOOL_METADATA = {
    "web_search": {
        "name": "web_search",
        "description": "Search the web for current information, tutorials, documentation, and resources",
        "parameters": {
            "query": {"type": "string", "description": "Search query"},
            "num_results": {"type": "integer", "description": "Number of results (default: 5)", "default": 5}
        },
        "returns": "List of search results with title, link, and snippet"
    },
    "search_documentation": {
        "name": "search_documentation",
        "description": "Search official documentation (Microsoft Learn, Python docs, etc.)",
        "parameters": {
            "topic": {"type": "string", "description": "Topic to search for"},
            "platform": {"type": "string", "description": "Platform: microsoft, azure, python, github", "default": "microsoft"},
            "num_results": {"type": "integer", "description": "Number of results (default: 3)", "default": 3}
        },
        "returns": "List of documentation links with descriptions"
    }
}


if __name__ == "__main__":
    # Test the search functionality
    print("[TEST] Web Search Tool\n")
    
    if not SERPAPI_KEY:
        print("[WARNING] SERPAPI_KEY not found in .env")
        print("Add: SERPAPI_KEY=your_key_here")
        print("Get free key at: https://serpapi.com\n")
    
    # Test web search
    print("Testing web_search()...")
    results = web_search("Azure Functions Python tutorial", num_results=3)
    print(format_search_results(results))
    
    # Test documentation search
    print("\nTesting search_documentation()...")
    docs = search_documentation("API authentication", "microsoft", num_results=2)
    print(format_search_results(docs, max_results=2))
    
    print("[TEST] Complete!")
