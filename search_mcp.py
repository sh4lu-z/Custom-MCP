import requests
from ddgs import DDGS
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Syntiox-Search-Tool")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 1: Web Search
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def web_search(query: str, num_results: int = 8) -> str:
    """
    Web search කරයි — title, snippet සහ URL ලබාදෙයි. Free, no API key.
    Use when user says: 'search', 'google X', 'search for X', 'X ගැන search කරන්න', 'find X online'.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))

        if not results:
            return f"🔍 '{query}' search results හමු නොවීය."

        output = f"🔍 WEB SEARCH: \"{query}\"\n{'═'*45}\n\n"
        for i, r in enumerate(results, 1):
            title   = r.get('title', 'No Title')
            url     = r.get('href', '')
            snippet = r.get('body', '')
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            output += (
                f"{i:02}. 🔵 {title}\n"
                f"     📝 {snippet}\n"
                f"     🔗 {url}\n"
                f"{'─'*45}\n"
            )
        return output
    except Exception as e:
        return f"❌ Search error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 2: News Search
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def search_news(query: str, num_results: int = 8) -> str:
    """
    Web news search කරයි — title, source, date, URL ලබාදෙයි.
    Use when user says: 'news about X', 'latest X news', 'X ගැන news හොයන්න'.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=num_results))

        if not results:
            return f"📰 '{query}' news හමු නොවීය."

        output = f"📰 NEWS SEARCH: \"{query}\"\n{'═'*45}\n\n"
        for i, r in enumerate(results, 1):
            title  = r.get('title', '')
            source = r.get('source', '')
            date   = r.get('date', '')[:10]
            url    = r.get('url', '')
            body   = r.get('body', '')[:150]
            output += (
                f"{i:02}. 🔵 {title}\n"
                f"     📝 {body}...\n"
                f"     📡 {source} | 🕐 {date}\n"
                f"     🔗 {url}\n"
                f"{'─'*45}\n"
            )
        return output
    except Exception as e:
        return f"❌ News search error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 3: Image Search
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def search_images(query: str, num_results: int = 5) -> str:
    """
    Image search කරයි — image URLs ලබාදෙයි.
    Use when user says: 'find images', 'image search', 'pictures of X', 'X ගේ photos'.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=num_results))

        if not results:
            return f"🖼️ '{query}' images හමු නොවීය."

        output = f"🖼️ IMAGE SEARCH: \"{query}\" — {len(results)} images\n{'═'*45}\n\n"
        for i, r in enumerate(results, 1):
            title  = r.get('title', 'No Title')
            url    = r.get('image', '')
            source = r.get('url', '')
            width  = r.get('width', '?')
            height = r.get('height', '?')
            output += (
                f"{i:02}. 🖼️  {title}\n"
                f"     📐 {width}x{height}\n"
                f"     🔗 {url}\n"
                f"     🌐 {source}\n"
                f"{'─'*45}\n"
            )
        return output
    except Exception as e:
        return f"❌ Image search error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 4: Site Search
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def search_site(query: str, site: str, num_results: int = 5) -> str:
    """
    Specific website ලෙ search කරයි (site: operator).
    Use when user says: 'search in site', 'find on website', 'stackoverflow ලෙ X search කරන්න'.
    Example: query='python list', site='stackoverflow.com'
    """
    try:
        full_query = f"site:{site} {query}"
        with DDGS() as ddgs:
            results = list(ddgs.text(full_query, max_results=num_results))

        if not results:
            return f"🔍 '{query}' — {site} ලෙ results හමු නොවීය."

        output = f"🔍 SEARCH ON {site.upper()}: \"{query}\"\n{'═'*45}\n\n"
        for i, r in enumerate(results, 1):
            title   = r.get('title', 'No Title')
            url     = r.get('href', '')
            snippet = r.get('body', '')[:180]
            output += (
                f"{i:02}. 🔵 {title}\n"
                f"     📝 {snippet}...\n"
                f"     🔗 {url}\n"
                f"{'─'*45}\n"
            )
        return output
    except Exception as e:
        return f"❌ Site search error: {e}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 5: Quick Answer / Definition
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def quick_answer(query: str) -> str:
    """
    Question ලෙ quick answer/definition ලබාගනී (DuckDuckGo Instant Answer).
    Use when user asks: 'what is X', 'define X', 'who is X', 'X කියන්නෙ මොකක්ද'.
    """
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            timeout=6
        ).json()

        abstract = resp.get("Abstract", "").strip()
        answer   = resp.get("Answer", "").strip()
        heading  = resp.get("Heading", "").strip()
        src      = resp.get("AbstractSource", "")
        src_url  = resp.get("AbstractURL", "")

        if not abstract and not answer:
            # Fallback to web search
            return web_search(query, num_results=3)

        output = f"💡 QUICK ANSWER: \"{query}\"\n{'═'*45}\n\n"
        if heading:
            output += f"📌 {heading}\n{'─'*45}\n"
        if answer:
            output += f"✅ {answer}\n\n"
        if abstract:
            output += f"{abstract}\n\n"
        if src:
            output += f"📚 Source: {src}\n🔗 {src_url}"
        return output

    except Exception as e:
        return f"❌ Quick answer error: {e}"


if __name__ == "__main__":
    mcp.run(transport='stdio')
