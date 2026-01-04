#!/usr/bin/env python3
"""
Serper MCP Server - A Model Context Protocol server for Serper.dev API
Provides Google Scholar search for academic papers
"""

import os
import json
import http.client
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables and validate SERPER_API_KEY
try:
    load_dotenv()
    
    serper_api_key = os.getenv("SERPER_API_KEY")
    if not serper_api_key:
        raise ValueError("SERPER_API_KEY environment variable is not set. Get your API key from https://serper.dev")
    
    SERPER_API_KEY = serper_api_key
except Exception as e:
    print(f"Error loading API key: {e}")
    raise

# Initialize MCP server
mcp = FastMCP("serper")


def search_scholar(query: str, num_results: int = 10) -> dict:
    """
    Search Google Scholar using Serper API
    
    Args:
        query: The academic search query
        num_results: Number of results to return (default: 10)
    
    Returns:
        dict: Search results from Serper API
    """
    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        
        payload = json.dumps({
            "q": query,
            "num": num_results
        })
        
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        conn.request("POST", "/scholar", payload, headers)
        res = conn.getresponse()
        data = res.read()
        
        if res.status != 200:
            return {
                "error": f"API request failed with status {res.status}",
                "details": data.decode("utf-8")
            }
        
        result = json.loads(data.decode("utf-8"))
        conn.close()
        
        return result
        
    except Exception as e:
        return {
            "error": "Search request failed",
            "details": str(e)
        }


@mcp.tool()
def google_search_scholar(query: str, num_results: int = 10) -> str:
    """
    Search Google Scholar for academic papers and research.
    Returns scholarly articles, citations, and related papers.
    
    Args:
        query: The academic search query
        num_results: Number of results to return (default: 10, max: 20)
    
    Returns:
        JSON string with search results including papers, citations, and metadata
    """
    if not query:
        return json.dumps({"error": "Query parameter is required"})
    
    # Limit num_results to max of 20 for Scholar
    num_results = min(num_results, 20)
    
    # Perform Google Scholar search
    result = search_scholar(query, num_results)
    
    # Format results
    if "error" in result:
        response = result
    else:
        # Extract scholarly paper information
        formatted_result = {
            "query": query,
            "search_type": "scholar",
            "papers": []
        }
        
        # Add search metadata if available
        if "searchParameters" in result:
            formatted_result["search_parameters"] = result["searchParameters"]
        
        # Format organic results as papers
        if "organic" in result:
            formatted_result["papers"] = result["organic"][:num_results]
        
        # Add related searches if available
        if "relatedSearches" in result:
            formatted_result["related_searches"] = result["relatedSearches"]
        
        response = formatted_result
    
    return json.dumps(response, indent=2)


if __name__ == "__main__":
     mcp.run(transport="sse", port=8001)


