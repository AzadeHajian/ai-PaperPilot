#!/usr/bin/env python3
"""
PubMed MCP Server - A Model Context Protocol server for PubMed API
Provides search and retrieval of biomedical and life sciences papers from PubMed
"""

import os
import json
from Bio import Entrez
from fastmcp import FastMCP
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
try:
    load_dotenv()
    
    # Set email for NCBI Entrez (required by NCBI's terms of service)
    ncbi_email = os.getenv("NCBI_EMAIL")
    if not ncbi_email:
        raise ValueError("NCBI_EMAIL environment variable is not set. Add your email to .env file")
    
    Entrez.email = ncbi_email
except Exception as e:
    print(f"Error loading NCBI email: {e}")
    raise

# Initialize MCP server
mcp = FastMCP("pubmed")


def search_pubmed(
    query: str,
    max_results: int = 10,
    sort: str = "relevance"
) -> dict:
    """
    Search PubMed for biomedical papers
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        sort: Sort order (relevance, pub_date, Author, JournalName)
    
    Returns:
        dict: Search results with paper PMIDs
    """
    try:
        # Search PubMed
        handle = Entrez.esearch(
            db="pubmed",
            term=query,
            retmax=max_results,
            sort=sort
        )
        results = Entrez.read(handle)
        handle.close()
        
        pmids = results.get("IdList", [])
        
        return {
            "query": query,
            "total_results": int(results.get("Count", 0)),
            "returned_results": len(pmids),
            "pmids": pmids
        }
        
    except Exception as e:
        return {
            "error": "PubMed search failed",
            "details": str(e)
        }


def get_paper_metadata(pmids: list) -> list:
    """
    Fetch metadata for PubMed articles
    
    Args:
        pmids: List of PubMed IDs
    
    Returns:
        list: List of paper metadata dictionaries
    """
    try:
        if not pmids:
            return []
        
        # Fetch details
        handle = Entrez.efetch(
            db="pubmed",
            id=",".join(pmids),
            rettype="medline",
            retmode="xml"
        )
        records = Entrez.read(handle)
        handle.close()
        
        papers = []
        for article in records.get("PubmedArticle", []):
            medline = article.get("MedlineCitation", {})
            article_data = medline.get("Article", {})
            
            # Extract authors
            authors = []
            author_list = article_data.get("AuthorList", [])
            for author in author_list:
                last_name = author.get("LastName", "")
                fore_name = author.get("ForeName", "")
                if last_name and fore_name:
                    authors.append(f"{fore_name} {last_name}")
                elif last_name:
                    authors.append(last_name)
            
            # Extract abstract
            abstract_texts = article_data.get("Abstract", {}).get("AbstractText", [])
            if isinstance(abstract_texts, list):
                abstract = " ".join([str(text) for text in abstract_texts])
            else:
                abstract = str(abstract_texts) if abstract_texts else ""
            
            # Extract publication date
            pub_date = article_data.get("ArticleDate", [{}])
            if pub_date and len(pub_date) > 0:
                date_info = pub_date[0]
                pub_year = date_info.get("Year", "")
                pub_month = date_info.get("Month", "")
                pub_day = date_info.get("Day", "")
                publication_date = f"{pub_year}-{pub_month}-{pub_day}" if pub_year else ""
            else:
                journal = article_data.get("Journal", {})
                journal_issue = journal.get("JournalIssue", {})
                pub_date_dict = journal_issue.get("PubDate", {})
                pub_year = pub_date_dict.get("Year", "")
                publication_date = pub_year
            
            # Extract journal
            journal_title = article_data.get("Journal", {}).get("Title", "")
            
            # Extract DOI
            article_ids = article.get("PubmedData", {}).get("ArticleIdList", [])
            doi = ""
            for article_id in article_ids:
                if article_id.attributes.get("IdType") == "doi":
                    doi = str(article_id)
                    break
            
            paper = {
                "pmid": medline.get("PMID", ""),
                "title": article_data.get("ArticleTitle", ""),
                "authors": authors,
                "abstract": abstract,
                "journal": journal_title,
                "publication_date": publication_date,
                "doi": doi,
                "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{medline.get('PMID', '')}/"
            }
            papers.append(paper)
        
        return papers
        
    except Exception as e:
        return [{
            "error": "Failed to fetch paper metadata",
            "details": str(e)
        }]


@mcp.tool()
def pubmed_search(
    query: str,
    max_results: int = 10,
    sort: str = "relevance"
) -> str:
    """
    Search PubMed for biomedical and life sciences papers.
    
    Args:
        query: Search query (can include keywords, author names, MeSH terms, etc.)
        max_results: Maximum number of papers to return (default: 10, max: 100)
        sort: Sort results by 'relevance', 'pub_date', 'Author', or 'JournalName' (default: 'relevance')
    
    Returns:
        JSON string with paper metadata including titles, authors, abstracts, DOIs, and PubMed links
    
    Examples:
        - "COVID-19 vaccine"
        - "cancer immunotherapy"
        - "CRISPR gene editing"
        - "Alzheimer's disease[MeSH]"
    """
    if not query:
        return json.dumps({"error": "Query parameter is required"})
    
    # Limit max_results to 100
    max_results = min(max_results, 100)
    
    # Perform search
    search_result = search_pubmed(query, max_results, sort)
    
    if "error" in search_result:
        return json.dumps(search_result, indent=2)
    
    # Fetch metadata for found papers
    pmids = search_result.get("pmids", [])
    papers = get_paper_metadata(pmids)
    
    result = {
        "query": query,
        "total_results": search_result.get("total_results", 0),
        "returned_results": len(papers),
        "papers": papers
    }
    
    return json.dumps(result, indent=2)


@mcp.tool()
def pubmed_get_paper_details(pmid: str) -> str:
    """
    Get detailed information about a specific PubMed paper by its PMID.
    
    Args:
        pmid: PubMed ID (e.g., "12345678")
    
    Returns:
        JSON string with detailed paper information including abstract, authors, journal, and DOI
    """
    if not pmid:
        return json.dumps({"error": "PMID parameter is required"})
    
    try:
        papers = get_paper_metadata([pmid])
        
        if papers and len(papers) > 0:
            return json.dumps(papers[0], indent=2)
        else:
            return json.dumps({"error": f"Paper with PMID '{pmid}' not found"})
        
    except Exception as e:
        return json.dumps({
            "error": "Failed to retrieve paper details",
            "details": str(e)
        })


@mcp.tool()
def pubmed_search_by_author(author_name: str, max_results: int = 10) -> str:
    """
    Search PubMed for papers by a specific author.
    
    Args:
        author_name: Author's name (e.g., "Smith J" or "John Smith")
        max_results: Maximum number of papers to return (default: 10, max: 100)
    
    Returns:
        JSON string with papers authored or co-authored by the specified person
    """
    if not author_name:
        return json.dumps({"error": "author_name parameter is required"})
    
    # Construct author query
    query = f"{author_name}[Author]"
    
    return pubmed_search(query, max_results, "pub_date")


@mcp.tool()
def pubmed_advanced_search(
    keywords: Optional[str] = None,
    author: Optional[str] = None,
    journal: Optional[str] = None,
    pub_date_from: Optional[str] = None,
    pub_date_to: Optional[str] = None,
    max_results: int = 10
) -> str:
    """
    Perform an advanced search on PubMed with multiple filters.
    
    Args:
        keywords: Keywords to search (optional)
        author: Author name to filter by (optional)
        journal: Journal name to filter by (optional)
        pub_date_from: Start date in format YYYY/MM/DD (optional)
        pub_date_to: End date in format YYYY/MM/DD (optional)
        max_results: Maximum number of papers to return (default: 10, max: 100)
    
    Returns:
        JSON string with filtered search results
    """
    # Build query
    query_parts = []
    
    if keywords:
        query_parts.append(keywords)
    
    if author:
        query_parts.append(f"{author}[Author]")
    
    if journal:
        query_parts.append(f"{journal}[Journal]")
    
    if pub_date_from and pub_date_to:
        query_parts.append(f"{pub_date_from}:{pub_date_to}[Date - Publication]")
    elif pub_date_from:
        query_parts.append(f"{pub_date_from}:3000[Date - Publication]")
    
    if not query_parts:
        return json.dumps({"error": "At least one search parameter is required"})
    
    query = " AND ".join(query_parts)
    
    return pubmed_search(query, max_results)


if __name__ == "__main__":
    mcp.run(transport="sse", port=8003)
