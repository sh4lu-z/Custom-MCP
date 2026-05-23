import requests
import xml.etree.ElementTree as ET
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Syntiox-News-Tool")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 1: Latest Sinhala News (Original)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_latest_news() -> str:
    """
    Fetches the latest 10 breaking news updates and headlines in Sinhala.
    Use this tool whenever the user asks for "news", "breaking news", "අලුත් පුවත්", "දේශපාලන පුවත්" or recent updates.
    """
    url = "https://esena-news-api-v3.vercel.app/"

    try:
        # API එකට කෝල් එකක් දමා JSON දත්ත ලබා ගැනීම
        response = requests.get(url, timeout=6)
        res_data = response.json()

        # JSON ව්‍යුහය අනුව දත්ත වෙන් කර ගැනීම (news_data -> data)
        news_list = res_data.get("news_data", {}).get("data", [])

        if not news_list:
            return "⚠️ මේ මොහොතේ ලබාගත හැකි පුවත් කිසිවක් හමු නොවීය."

        output = "📰 *LATEST NEWS UPDATES (Esena News API)*\n\n"

        # උපරිම පුවත් 10ක් පමණක් ලූපය හරහා ලබා ගැනීම
        for i, news in enumerate(news_list[:10], 1):
            title_si = news.get("titleSi", "මාතෘකාවක් නොමැත")
            news_id  = news.get("id", "N/A")

            output += f"{i}. 📌 *{title_si}* (ID: {news_id})\n"

            # contentSi එක ඇතුළේ තියෙන ඡේද (Paragraphs) වලින් පළමු කොටස ලබා ගැනීම
            content_blocks = news.get("contentSi", [])
            if content_blocks and isinstance(content_blocks, list):
                first_block = content_blocks[0]
                if isinstance(first_block, dict) and "data" in first_block:
                    snippet = first_block["data"]
                    # විස්තරය ගොඩක් දිග නම් අකුරු 180කට සීමා කිරීම (Context එක ඉතිරි කර ගැනීමට)
                    if len(snippet) > 180:
                        snippet = snippet[:180] + "..."
                    output += f"📝 {snippet}\n"

            output += "––––––––––––––––––––––––\n"

        return output

    except Exception as e:
        return f"❌ පුවත් සේවාදායකය සමඟ සම්බන්ධ වීමට නොහැකි විය. Error: {str(e)}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 2: Search Sinhala News
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def search_sinhala_news(keyword: str) -> str:
    """
    Sinhala news keyword සෙව්ම (Esena News API).
    Use for: 'find sinhala news about X', 'X ගැන ලංකා පුවත්', 'search news'.
    """
    url = "https://esena-news-api-v3.vercel.app/"

    try:
        response  = requests.get(url, timeout=6)
        res_data  = response.json()
        news_list = res_data.get("news_data", {}).get("data", [])

        found = [
            n for n in news_list
            if keyword.lower() in n.get("titleSi", "").lower()
            or keyword.lower() in n.get("titleEn", "").lower()
        ]

        if not found:
            return f"🔍 '{keyword}' සඳහා Sinhala news හමු නොවීය."

        output = f"🔍 *NEWS SEARCH: '{keyword}'* — {len(found)} results\n\n"
        for i, news in enumerate(found[:8], 1):
            title_si = news.get("titleSi", "?")
            news_id  = news.get("id", "N/A")
            output  += f"{i}. 📌 *{title_si}* (ID: {news_id})\n"

            content_blocks = news.get("contentSi", [])
            if content_blocks and isinstance(content_blocks, list):
                first_block = content_blocks[0]
                if isinstance(first_block, dict) and "data" in first_block:
                    snippet = first_block["data"]
                    if len(snippet) > 150:
                        snippet = snippet[:150] + "..."
                    output += f"📝 {snippet}\n"

            output += "––––––––––––––––––––––––\n"
        return output

    except Exception as e:
        return f"❌ Search error: {str(e)}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOOL 3: World News (Google News RSS)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@mcp.tool()
def get_world_news(category: str = "top", max_results: int = 8) -> str:
    """
    World / English news (Google News RSS) ලබාගනී.
    Use for: 'world news', 'international news', 'global news', 'english news'.
    Available categories: top, technology, business, sports, health, entertainment, science, world
    """
    urls = {
        "top"          : "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        "technology"   : "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGxqTjNjd1NHdGlkR1J5TlRBQVAB?hl=en-US&gl=US&ceid=US:en",
        "business"     : "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlBQVAB?hl=en-US&gl=US&ceid=US:en",
        "sports"       : "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnVHZ0pWVXlBQVAB?hl=en-US&gl=US&ceid=US:en",
        "health"       : "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNR3QwTlRFU0FtVnVLQUFQAQ?hl=en-US&gl=US&ceid=US:en",
        "entertainment": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnVHZ0pWVXlBQVAB?hl=en-US&gl=US&ceid=US:en",
        "science"      : "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0YVhjU0FtVnVHZ0pWVXlBQVAB?hl=en-US&gl=US&ceid=US:en",
        "world"        : "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlBQVAB?hl=en-US&gl=US&ceid=US:en",
    }
    cat = category.lower().strip()
    if cat not in urls:
        return f"❌ Category '{category}' නොමැත. Use: {', '.join(urls.keys())}"

    try:
        resp  = requests.get(urls[cat], timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        root  = ET.fromstring(resp.content)
        items = root.findall('.//item')[:max_results]

        emoji_map = {
            "top":"🌍","technology":"💻","business":"💼","sports":"⚽",
            "health":"🏥","entertainment":"🎬","science":"🔬","world":"🌐"
        }
        output = f"📰 *WORLD NEWS — {cat.upper()}* {emoji_map.get(cat,'')}\n\n"
        for i, item in enumerate(items, 1):
            title  = item.findtext('title', '').strip()
            pub    = item.findtext('pubDate', '')[:25]
            source = item.findtext('source', '')
            if ' - ' in title:
                parts  = title.rsplit(' - ', 1)
                title  = parts[0].strip()
                source = source or parts[1].strip()
            output += (
                f"{i}. 📌 *{title}*\n"
                f"   📡 {source} | 🕐 {pub}\n"
                f"––––––––––––––––––––––––\n"
            )
        return output
    except Exception as e:
        return f"❌ World news error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport='stdio')