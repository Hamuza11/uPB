"""
JTI License v2.0

This software is provided "as is", without warranty of any kind.

You are free to use, modify, and share this software,
but please give credit to the original author, Hamza.

No commercial use without explicit permission.

Have fun and keep hacking! 😎

© 2025 Hamza
"""


import urequests
import network
import time

# --- WiFi setup ---
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    print("Connecting to WiFi", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\nConnected:", wlan.ifconfig())

# --- Wikipedia summary ---
def fetch_wiki_summary(query):
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + query
    try:
        response = urequests.get(url)
        data = response.json()
        response.close()
        return data.get("title", "No Title"), data.get("extract", "No content.")
    except Exception as e:
        return "Error", "Could not fetch data: " + str(e)

# --- DuckDuckGo instant answer ---
def fetch_ddg_result(query):
    base_url = "https://api.duckduckgo.com/"
    params = "?q=" + query.replace(" ", "+") + "&format=json&no_html=1"
    try:
        response = urequests.get(base_url + params)
        data = response.json()
        response.close()

        title = data.get("Heading", "DuckDuckGo Search")
        summary = data.get("AbstractText", "No direct answer found.")

        if not summary and data.get("RelatedTopics"):
            summary = data["RelatedTopics"][0].get("Text", "No summary.")

        return title, summary
    except Exception as e:
        return "Error", "DuckDuckGo fetch failed: " + str(e)

# --- XKCD comic fetcher ---
def fetch_xkcd(comic_number=None):
    if comic_number:
        url = f"https://xkcd.com/{comic_number}/info.0.json"
    else:
        url = "https://xkcd.com/info.0.json"
    try:
        response = urequests.get(url)
        data = response.json()
        response.close()

        num = data.get("num", "???")
        title = data.get("title", "No title")
        alt = data.get("alt", "")
        return f"#{num} - {title}", alt
    except Exception as e:
        return "Error", "XKCD fetch failed: " + str(e)

# --- Hacker News top stories ---
def fetch_hn_top(n=5):
    base_url = "https://hacker-news.firebaseio.com/v0"
    try:
        top_resp = urequests.get(f"{base_url}/topstories.json")
        top_ids = top_resp.json()[:n]
        top_resp.close()

        stories = []
        for story_id in top_ids:
            item_resp = urequests.get(f"{base_url}/item/{story_id}.json")
            item = item_resp.json()
            item_resp.close()

            title = item.get("title", "No title")
            url = item.get("url", "No URL")
            stories.append(f"- {title}\n  {url}")

        return "\n\n".join(stories)
    except Exception as e:
        return "Error fetching Hacker News: " + str(e)

# --- Main uPB CLI loop ---
def upb_main():
    print("=== uPB v1.0 (MicroPython JSON Browser) ===")
    print("Commands: search <term>, ddg <query>, xkcd [num], hn, reload, quit\n")

    current_term = "MicroPython"

    while True:
        cmd = input("uPB> ").strip()

        if cmd.startswith("search "):
            current_term = cmd[7:].strip().replace(" ", "_")
        elif cmd == "":
            continue
        elif cmd == "reload":
            pass  # Just fetch current_term again
        elif cmd == "quit":
            print("Bye!")
            break
        elif cmd.startswith("ddg "):
            current_term = cmd[4:].strip()
            print("Searching DuckDuckGo:", current_term)
            title, extract = fetch_ddg_result(current_term)
            print("\n=== " + title + " ===")
            print(extract + "\n")
            continue
        elif cmd.startswith("xkcd"):
            parts = cmd.split()
            if len(parts) == 2 and parts[1].isdigit():
                title, text = fetch_xkcd(int(parts[1]))
            else:
                title, text = fetch_xkcd()
            print("\n=== " + title + " ===")
            print(text + "\n")
            continue
        elif cmd == "hn":
            print("\n=== Hacker News Top ===")
            print(fetch_hn_top(5) + "\n")
            continue
        else:
            print("Unknown command. Use: search <term>, ddg <query>, xkcd [num], hn, reload, or quit.")
            continue

        # Default: fetch Wikipedia summary for current_term
        print("Fetching:", current_term)
        title, extract = fetch_wiki_summary(current_term)
        print("\n=== " + title + " ===")
        print(extract + "\n")

# === Replace these with your Wi-Fi creds ===
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASS = "YOUR_WIFI_PASSWORD"

# === Run it ===
connect_wifi(WIFI_SSID, WIFI_PASS)
upb_main()
