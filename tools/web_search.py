"""
Web Search Tool for StudyMate AI Agents

Provides web search capabilities using SerpAPI (Google Search).
Agents can use this to find latest documentation, tutorials, and resources.
"""

import os
import requests
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SEARCH_TIMEOUT_SECONDS = float(os.getenv("STUDYMATE_SEARCH_TIMEOUT_SECONDS", "15"))


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
        return []
    
    try:
        # SerpAPI endpoint
        url = "https://serpapi.com/search"
        
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": num_results,
            "engine": "google"
        }
        
        response = requests.get(url, params=params, timeout=SEARCH_TIMEOUT_SECONDS)
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
        return results
        
    except requests.exceptions.RequestException as e:
        return []
    except Exception as e:
        return []



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
