#!/usr/bin/env python3
import os
import sys
import urllib.parse
import feedparser
import yaml
import requests
import datetime
import logging
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("STEMNewsBot")

def load_config(config_path="config.yaml"):
    """Load configurations from yaml file."""
    if not os.path.exists(config_path):
        logger.error(f"Configuration file {config_path} not found.")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def fetch_google_news(query, limit=10):
    """Fetch the latest Google News items from RSS feed."""
    encoded_query = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    logger.info(f"Fetching RSS feed from: {rss_url}")
    try:
        feed = feedparser.parse(rss_url)
        entries = feed.entries[:limit]
        news_items = []
        
        for entry in entries:
            news_items.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": entry.get("source", {}).get("title", "Unknown Source"),
                "description": entry.get("summary", "")
            })
        logger.info(f"Successfully fetched {len(news_items)} news items from Google News.")
        return news_items
    except Exception as e:
        logger.error(f"Error fetching RSS feed: {e}")
        return []

def generate_summary(news_items, query, api_key, model_name="gemini-2.5-flash"):
    """Use Gemini API to summarize the news items in the requested format."""
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.warning("Gemini API Key is missing or using placeholder value. Operating in DRY RUN mode.")
        mock_summary = f"""# AI + STEM Education Daily Brief

## Key Developments
- **Example Development**: This is a dry-run placeholder because no valid GEMINI_API_KEY was provided. Found {len(news_items)} news items for '{query}'.
- **News Item 1**: {news_items[0]['title'] if news_items else 'No news available'}

## Implications for Educators
- **Dry-run advice**: Please configure your real Gemini API key in the .env file to generate professional AI insights.
"""
        return mock_summary, "DRY RUN"

    # Construct prompt
    prompt = f"You are an expert AI and STEM Education researcher and advisor.\n"
    prompt += f"Here are the latest {len(news_items)} news articles related to '{query}':\n\n"
    
    for idx, item in enumerate(news_items, 1):
        prompt += f"--- Article {idx} ---\n"
        prompt += f"Title: {item['title']}\n"
        prompt += f"Source: {item['source']}\n"
        prompt += f"Published: {item['published']}\n"
        prompt += f"Link: {item['link']}\n"
        prompt += f"Summary/Snippet: {item['description']}\n\n"
        
    prompt += """Please read the above articles and generate a synthesis/brief in exactly the following markdown format:

# AI + STEM Education Daily Brief

## Key Developments
- [Write bullet points summarizing the most important advancements, news, and trends from the articles. Focus on facts, achievements, and technology.]
- [Keep each point professional, concise, and informative.]

## Implications for Educators
- [Write bullet points highlighting what these developments mean for educators, classrooms, curricula, and STEM learning.]
- [Provide actionable insights and professional advice based on the developments.]

Constraints:
1. Do not use any introductory or concluding filler text. Output ONLY the markdown format shown above starting directly with '# AI + STEM Education Daily Brief'.
2. Rely only on the provided articles. Do not invent facts outside of them, but synthesize their information intelligently.
3. Keep the language concise and clear.
"""

    logger.info(f"Generating summary using Gemini API (model: {model_name})...")
    try:
        # Initialize the client using modern google-genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        logger.info("Gemini API call completed successfully.")
        return response.text, "SUCCESS"
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return None, "FAILED"

def save_brief_to_archive(content, tz_hours=8):
    """Save the markdown brief to archive folder with current date."""
    try:
        os.makedirs("archive", exist_ok=True)
        # Default is Beijing Time (UTC+8)
        tz_offset = datetime.timezone(datetime.timedelta(hours=tz_hours))
        now_tz = datetime.datetime.now(tz_offset)
        filename = f"archive/{now_tz.strftime('%Y-%m-%d')}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Daily brief saved to archive: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to save brief to archive: {e}")
        return None

def send_to_discord(webhook_url, content):
    """Send content to Discord Webhook."""
    if not webhook_url or webhook_url in ["your_discord_webhook_url_here", ""]:
        logger.warning("Discord Webhook URL is missing or using placeholder. Skipped sending to Discord.")
        logger.info("Printing content to standard output instead:\n")
        logger.info("="*40 + "\n" + content + "\n" + "="*40)
        return "SKIPPED"
    
    # Discord messages are limited to 2000 characters
    if len(content) > 2000:
        logger.warning("Content exceeds 2000 characters. Truncating for Discord message limits...")
        content = content[:1990] + "\n...(truncated)"
        
    payload = {
        "content": content
    }
    
    logger.info("Sending brief to Discord Webhook...")
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code in [200, 204]:
            logger.info("Successfully sent brief to Discord!")
            return "SUCCESS"
        else:
            logger.error(f"Failed to send to Discord. Status code: {response.status_code}. Response: {response.text}")
            return "FAILED"
    except Exception as e:
        logger.error(f"Error sending to Discord Webhook: {e}")
        return "FAILED"

def main():
    logger.info("=== Bot Run Initiated ===")
    
    # 1. Load Config
    config = load_config()
    query = config.get("search", {}).get("query", "AI STEM Education")
    limit = config.get("search", {}).get("limit", 10)
    model_name = config.get("gemini", {}).get("model_name", "gemini-2.5-flash")
    
    # 2. Fetch News from Google News RSS
    news_items = fetch_google_news(query, limit)
    
    if not news_items:
        logger.error("No news articles found. Bot run terminated prematurely.")
        return False
        
    logger.info(f"Found {len(news_items)} news items.")
    
    # 3. Get API Keys from env / config
    gemini_key = os.getenv("GEMINI_API_KEY")
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL") or config.get("discord", {}).get("webhook_url")
    
    # 4. Generate Summary with Gemini
    summary, gemini_status = generate_summary(news_items, query, gemini_key, model_name)
    
    if not summary:
        logger.error("Failed to generate summary. Bot run terminated prematurely.")
        return False
        
    # 5. Archive the brief
    save_brief_to_archive(summary)
    
    # 6. Send to Discord
    discord_status = send_to_discord(discord_webhook, summary)
    
    logger.info(f"=== Bot Run Completed [News: {len(news_items)}, Gemini: {gemini_status}, Discord: {discord_status}] ===")
    return True

if __name__ == "__main__":
    main()
