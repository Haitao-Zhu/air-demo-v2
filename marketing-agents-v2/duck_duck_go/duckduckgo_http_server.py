#!/usr/bin/env python3
"""
DuckDuckGo MCP Server using FastMCP
Provides DuckDuckGo search functionality exposed on /mcp endpoint

Original source adapted from nickclyde/duckduckgo-mcp-server under MIT licence
"""

import argparse
import asyncio
import json
import re
import sys
import time
import traceback
import urllib.parse
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup  # pyright: ignore[reportMissingImports]
from fastmcp import Context, FastMCP  # pyright: ignore[reportMissingImports]


@dataclass
class RequestLog:
    """Represents a logged request with metadata"""

    timestamp: datetime
    method: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[str] = None
    response_content: Optional[str] = None  # Full response content
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    session_id: Optional[str] = None


class SessionRequestLogger:
    """Manages request logging per session"""

    def __init__(self, max_logs_per_session: int = 100):
        self.sessions: Dict[str, List[RequestLog]] = defaultdict(list)
        self.max_logs_per_session = max_logs_per_session
        self.active_sessions: Dict[str, str] = {}  # Maps connection ID to session ID

    def create_session(self) -> str:
        """Create a new session ID"""
        session_id = str(uuid.uuid4())
        return session_id

    def log_request(self, session_id: str, log: RequestLog):
        """Add a request log to a session"""
        log.session_id = session_id
        session_logs = self.sessions[session_id]
        session_logs.append(log)

        # Keep only the most recent logs
        if len(session_logs) > self.max_logs_per_session:
            self.sessions[session_id] = session_logs[-self.max_logs_per_session :]

    def get_session_logs(self, session_id: str) -> List[RequestLog]:
        """Get all logs for a session"""
        return self.sessions.get(session_id, [])

    def clear_session(self, session_id: str):
        """Clear logs for a specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]


@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str
    position: int


class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = []

    async def acquire(self):
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [
            req for req in self.requests if now - req < timedelta(minutes=1)
        ]

        if len(self.requests) >= self.requests_per_minute:
            # Wait until we can make another request
            wait_time = 60 - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self.requests.append(now)


class DuckDuckGoSearcher:
    BASE_URL = "https://html.duckduckgo.com/html"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def __init__(self):
        self.rate_limiter = RateLimiter()

    def format_results_for_llm(self, results: List[SearchResult]) -> str:
        """Format results in a natural language style that's easier for LLMs to process"""
        if not results:
            return "No results were found for your search query. This could be due to DuckDuckGo's bot detection or the query returned no matches. Please try rephrasing your search or try again in a few minutes."

        output = []
        output.append(f"Found {len(results)} search results:\n")

        for result in results:
            output.append(f"{result.position}. {result.title}")
            output.append(f"   URL: {result.link}")
            output.append(f"   Summary: {result.snippet}")
            output.append("")  # Empty line between results

        return "\n".join(output)

    async def search(
        self, query: str, ctx: Optional[Context], max_results: int = 10
    ) -> List[SearchResult]:
        try:
            # Apply rate limiting
            await self.rate_limiter.acquire()

            # Create form data for POST request
            data = {
                "q": query,
                "b": "",
                "kl": "",
            }

            if ctx:
                await ctx.info(f"Searching DuckDuckGo for: {query}")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL, data=data, headers=self.HEADERS, timeout=30.0
                )
                response.raise_for_status()

            # Parse HTML response
            soup = BeautifulSoup(response.text, "html.parser")
            if not soup:
                if ctx:
                    await ctx.error("Failed to parse HTML response")
                return []

            results = []
            for result in soup.select(".result"):
                title_elem = result.select_one(".result__title")
                if not title_elem:
                    continue

                link_elem = title_elem.find("a")
                if not link_elem:
                    continue

                title = link_elem.get_text(strip=True)
                # Ensure link is a string
                link_attr = link_elem.get("href", "") if hasattr(link_elem, "get") else ""  # type: ignore
                link = str(link_attr) if link_attr else ""

                # Skip ad results
                if "y.js" in link:
                    continue

                # Clean up DuckDuckGo redirect URLs
                if link.startswith("//duckduckgo.com/l/?uddg="):
                    link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])

                snippet_elem = result.select_one(".result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                results.append(
                    SearchResult(
                        title=title,
                        link=link,
                        snippet=snippet,
                        position=len(results) + 1,
                    )
                )

                if len(results) >= max_results:
                    break

            if ctx:
                await ctx.info(f"Successfully found {len(results)} results")
            return results

        except httpx.TimeoutException:
            if ctx:
                await ctx.error("Search request timed out")
            return []
        except httpx.HTTPError as e:
            if ctx:
                await ctx.error(f"HTTP error occurred: {str(e)}")
            return []
        except Exception as e:
            if ctx:
                await ctx.error(f"Unexpected error during search: {str(e)}")
            traceback.print_exc(file=sys.stderr)
            return []


class WebContentFetcher:
    def __init__(self):
        self.rate_limiter = RateLimiter(requests_per_minute=20)

    async def fetch_and_parse(self, url: str, ctx: Optional[Context]) -> str:
        """Fetch and parse content from a webpage"""
        try:
            await self.rate_limiter.acquire()

            if ctx:
                await ctx.info(f"Fetching content from: {url}")

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    follow_redirects=True,
                    timeout=30.0,
                )
                response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "header", "footer"]):
                element.decompose()

            # Get the text content
            text = soup.get_text()

            # Clean up the text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            # Remove extra whitespace
            text = re.sub(r"\s+", " ", text).strip()

            # Truncate if too long
            if len(text) > 8000:
                text = text[:8000] + "... [content truncated]"

            if ctx:
                await ctx.info(
                    f"Successfully fetched and parsed content ({len(text)} characters)"
                )
            return text

        except httpx.TimeoutException:
            if ctx:
                await ctx.error(f"Request timed out for URL: {url}")
            return "Error: The request timed out while trying to fetch the webpage."
        except httpx.HTTPError as e:
            if ctx:
                await ctx.error(f"HTTP error occurred while fetching {url}: {str(e)}")
            return f"Error: Could not access the webpage ({str(e)})"
        except Exception as e:
            if ctx:
                await ctx.error(f"Error fetching content from {url}: {str(e)}")
            return f"Error: An unexpected error occurred while fetching the webpage ({str(e)})"


# Initialize FastMCP server and request logger
mcp = FastMCP("DuckDuckGoServer")
searcher = DuckDuckGoSearcher()
fetcher = WebContentFetcher()
request_logger = SessionRequestLogger()

# Store for session tracking
SESSION_STORE = {}


@mcp.tool
async def search_web(
    query: str, max_results: int = 10, ctx: Optional[Context] = None
) -> str:
    """
    Search DuckDuckGo and return formatted results.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default: 10)
        ctx: FastMCP context for session tracking
    """
    start_time = time.time()

    # Get session ID from context (this should be the client session ID)
    session_id = None
    if ctx:
        try:
            # session_id is a property, not a method
            session_id = ctx.session_id
            print(f"DEBUG: Got session ID from context: {session_id}")
        except Exception as e:
            print(f"DEBUG: Failed to get session ID from context: {e}")
            # If context doesn't provide session ID, generate one
            session_id = request_logger.create_session()
    else:
        session_id = "unknown"

    # Create request log
    request_log = RequestLog(
        timestamp=datetime.now(),
        method="search_web",
        tool_name="search_web",
        arguments={"query": query, "max_results": max_results},
        session_id=session_id,
    )

    try:
        # Log the request start
        if ctx:
            await ctx.info(f"[Session {session_id}] Starting web search for: {query}")

        results = await searcher.search(query, ctx, max_results)
        formatted = searcher.format_results_for_llm(results)

        # Update request log with success
        request_log.result = f"Found {len(results)} results"
        request_log.response_content = formatted  # Save full response
        request_log.duration_ms = (time.time() - start_time) * 1000

        if ctx:
            await ctx.info(
                f"[Session {session_id}] Search completed in {request_log.duration_ms:.2f}ms"
            )

        # Store session ID for debugging
        SESSION_STORE[session_id] = datetime.now().isoformat()
        print(f"DEBUG: Session {session_id} stored in SESSION_STORE")

        return formatted

    except Exception as e:
        # Update request log with error
        request_log.error = str(e)
        request_log.duration_ms = (time.time() - start_time) * 1000

        if ctx:
            await ctx.error(f"[Session {session_id}] Search failed: {str(e)}")

        traceback.print_exc(file=sys.stderr)
        return f"An error occurred while searching: {str(e)}"
    finally:
        # Log the request
        request_logger.log_request(session_id, request_log)


@mcp.tool
async def fetch_webpage_content(url: str, ctx: Optional[Context] = None) -> str:
    """
    Fetch and parse content from a webpage URL.

    Args:
        url: The webpage URL to fetch content from
        ctx: FastMCP context for session tracking
    """
    start_time = time.time()

    # Get session ID from context (this should be the client session ID)
    session_id = None
    if ctx:
        try:
            # session_id is a property, not a method
            session_id = ctx.session_id
            print(f"DEBUG: Got session ID from context: {session_id}")
        except Exception as e:
            print(f"DEBUG: Failed to get session ID from context: {e}")
            # If context doesn't provide session ID, generate one
            session_id = request_logger.create_session()
    else:
        session_id = "unknown"

    # Create request log
    request_log = RequestLog(
        timestamp=datetime.now(),
        method="fetch_webpage_content",
        tool_name="fetch_webpage_content",
        arguments={"url": url},
        session_id=session_id,
    )

    try:
        # Log the request start
        if ctx:
            await ctx.info(f"[Session {session_id}] Starting webpage fetch for: {url}")

        content = await fetcher.fetch_and_parse(url, ctx)

        # Update request log with success
        request_log.result = f"Fetched {len(content)} characters"
        request_log.response_content = (
            content[:2000] + "..." if len(content) > 2000 else content
        )  # Save truncated response
        request_log.duration_ms = (time.time() - start_time) * 1000

        if ctx:
            await ctx.info(
                f"[Session {session_id}] Fetch completed in {request_log.duration_ms:.2f}ms"
            )

        return content

    except Exception as e:
        # Update request log with error
        request_log.error = str(e)
        request_log.duration_ms = (time.time() - start_time) * 1000

        if ctx:
            await ctx.error(f"[Session {session_id}] Fetch failed: {str(e)}")

        traceback.print_exc(file=sys.stderr)
        return f"An error occurred while fetching content: {str(e)}"
    finally:
        # Log the request
        request_logger.log_request(session_id, request_log)


@mcp.tool
async def get_session_logs(session_id: str) -> str:
    """
    Retrieve complete request and response logs for a specific session.

    Args:
        session_id: Required session ID to retrieve logs for
    """
    # Validate session_id
    if not session_id:
        return "Error: session_id is required. Please provide a valid session ID."

    # Get logs for specific session
    logs = request_logger.get_session_logs(session_id)
    if not logs:
        return f"No logs found for session {session_id}"

    output = [f"=" * 80]
    output.append(f"SESSION LOGS: {session_id}")
    output.append(f"Total Requests: {len(logs)}")
    output.append(f"=" * 80 + "\n")

    for i, log in enumerate(logs, 1):
        output.append(f"REQUEST #{i}")
        output.append("-" * 40)
        output.append(f"Timestamp: {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"Tool: {log.tool_name}")
        output.append(
            f"Duration: {log.duration_ms:.2f}ms" if log.duration_ms else "Duration: N/A"
        )

        # Show request details
        output.append(f"\nREQUEST PARAMETERS:")
        output.append(json.dumps(log.arguments, indent=2))

        # Show full response
        if log.error:
            output.append(f"\nERROR:")
            output.append(f"{log.error}")
        elif log.response_content:
            output.append(f"\nFULL RESPONSE:")
            output.append(log.response_content)
        else:
            output.append("\nRESPONSE: No content saved")

        output.append("\n" + "=" * 80 + "\n")

    return "\n".join(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DuckDuckGo MCP Server")
    parser.add_argument(
        "--port", type=int, default=4003, help="Port to run the server on"
    )
    args = parser.parse_args()

    print(f"Starting DuckDuckGo Server on http://127.0.0.1:{args.port}/mcp")
    print(f"Server provides search tools via HTTP on /mcp endpoint")
    print("Available tools: search_web, fetch_webpage_content, get_session_logs")
    print(f"Session tracking enabled - sessions stored: {len(SESSION_STORE)}")

    # Run with HTTP transport on /mcp endpoint
    mcp.run(transport="http", host="127.0.0.1", port=args.port, path="/mcp")
