#!/usr/bin/env python3
"""
Serper MCP Server - A Model Context Protocol server for Serper.dev API
Provides Google search capabilities through Serper.dev
"""

import os
import sys
import json
import http.client
import asyncio
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize MCP server
app = Server("serper-search")

# Validate SERPER_API_KEY environment variable
serper_api_key = os.getenv("SERPER_API_KEY")
if not serper_api_key:
    raise ValueError("SERPER_API_KEY environment variable is not set. Get your API key from https://serper.dev")

SERPER_API_KEY = serper_api_key


def search_serper(query: str, search_type: str = "search", num_results: int = 10) -> dict:
    """
    Perform a search using Serper API
    
    Args:
        query: The search query
        search_type: Type of search (search, images, videos, news, places, shopping)
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
        
        # Map search type to endpoint
        endpoint = f"/{search_type}"
        
        conn.request("POST", endpoint, payload, headers)
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


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Serper search tools"""
    return [
        Tool(
            name="google_search_scholar",
            description="Search Google Scholar for academic papers and research using Serper API. Returns scholarly articles, citations, and related papers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The academic search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10, max: 20)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for Google Scholar searches"""
    
    query = arguments.get("query")
    num_results = arguments.get("num_results", 10)
    
    if not query:
        return [TextContent(
            type="text",
            text=json.dumps({"error": "Query parameter is required"})
        )]
    
    # Perform Google Scholar search
    result = search_serper(query, "scholar", num_results)
    
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
    
    return [TextContent(
        type="text",
        text=json.dumps(response, indent=2)
    )]


async def main():
    """Run the Serper MCP server"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

