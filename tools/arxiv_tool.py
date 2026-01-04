#!/usr/bin/env python3
"""
arXiv MCP Server - A Model Context Protocol server for arXiv API
Provides search and retrieval of academic papers from arXiv.org
"""

import json
import arxiv
from fastmcp import FastMCP
from typing import Optional

# Initialize MCP server
mcp = FastMCP("arxiv")


def search_arxiv(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance"
) -> dict:
    """
    Search arXiv for academic papers
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        sort_by: Sort order (relevance, lastUpdatedDate, submittedDate)
    
    Returns:
        dict: Search results with paper metadata
    """
    try:
        # Map sort_by string to arxiv.SortCriterion
        sort_map = {
            "relevance": arxiv.SortCriterion.Relevance,
            "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
            "submittedDate": arxiv.SortCriterion.SubmittedDate
        }
        
        sort_criterion = sort_map.get(sort_by, arxiv.SortCriterion.Relevance)
        
        # Create search
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=sort_criterion
        )
        
        # Execute search and collect results
        papers = []
        for result in search.results():
            paper = {
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "published": result.published.isoformat(),
                "updated": result.updated.isoformat(),
                "summary": result.summary,
                "pdf_url": result.pdf_url,
                "entry_id": result.entry_id,
                "arxiv_id": result.get_short_id(),
                "primary_category": result.primary_category,
                "categories": result.categories,
                "links": [link.href for link in result.links]
            }
            papers.append(paper)
        
        return {
            "query": query,
            "total_results": len(papers),
            "papers": papers
        }
        
    except Exception as e:
        return {
            "error": "arXiv search failed",
            "details": str(e)
        }


@mcp.tool()
def arxiv_search(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance"
) -> str:
    """
    Search arXiv for academic papers in computer science, physics, mathematics, and more.
    
    Args:
        query: Search query (can include keywords, author names, titles, etc.)
        max_results: Maximum number of papers to return (default: 10, max: 50)
        sort_by: Sort results by 'relevance', 'lastUpdatedDate', or 'submittedDate' (default: 'relevance')
    
    Returns:
        JSON string with paper metadata including titles, authors, abstracts, PDF links, and categories
    
    Examples:
        - "machine learning"
        - "au:Hinton AND ti:neural networks"
        - "cat:cs.AI"
    """
    if not query:
        return json.dumps({"error": "Query parameter is required"})
    
    # Limit max_results to 50
    max_results = min(max_results, 50)
    
    # Perform search
    result = search_arxiv(query, max_results, sort_by)
    
    return json.dumps(result, indent=2)


@mcp.tool()
def arxiv_get_paper_details(arxiv_id: str) -> str:
    """
    Get detailed information about a specific arXiv paper by its ID.
    
    Args:
        arxiv_id: arXiv paper ID (e.g., "2301.07041" or "arXiv:2301.07041")
    
    Returns:
        JSON string with detailed paper information including abstract, authors, and links
    """
    if not arxiv_id:
        return json.dumps({"error": "arxiv_id parameter is required"})
    
    try:
        # Remove "arXiv:" prefix if present
        arxiv_id = arxiv_id.replace("arXiv:", "").strip()
        
        # Search by ID
        search = arxiv.Search(id_list=[arxiv_id])
        result = next(search.results())
        
        paper = {
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "published": result.published.isoformat(),
            "updated": result.updated.isoformat(),
            "summary": result.summary,
            "pdf_url": result.pdf_url,
            "entry_id": result.entry_id,
            "arxiv_id": result.get_short_id(),
            "primary_category": result.primary_category,
            "categories": result.categories,
            "comment": result.comment,
            "journal_ref": result.journal_ref,
            "doi": result.doi,
            "links": [link.href for link in result.links]
        }
        
        return json.dumps(paper, indent=2)
        
    except StopIteration:
        return json.dumps({"error": f"Paper with ID '{arxiv_id}' not found"})
    except Exception as e:
        return json.dumps({
            "error": "Failed to retrieve paper details",
            "details": str(e)
        })


@mcp.tool()
def arxiv_search_by_author(author_name: str, max_results: int = 10) -> str:
    """
    Search arXiv for papers by a specific author.
    
    Args:
        author_name: Author's name (e.g., "Geoffrey Hinton" or "Hinton")
        max_results: Maximum number of papers to return (default: 10, max: 50)
    
    Returns:
        JSON string with papers authored or co-authored by the specified person
    """
    if not author_name:
        return json.dumps({"error": "author_name parameter is required"})
    
    # Construct author query
    query = f"au:{author_name}"
    
    return arxiv_search(query, max_results, "submittedDate")


if __name__ == "__main__":
    mcp.run(transport="sse", port=8002)
