"""
JTI License v2.0

This software is provided "as is", without warranty of any kind.

You are free to use, modify, and share this software,
but please give credit to the original author, Hamza.

No commercial use without explicit permission.

Have fun and keep hacking! 😎

© 2025 Hamza
"""

from __future__ import annotations

# Standard library imports
import sys
import time
from typing import Any, Dict, Tuple

# Try to support both MicroPython and CPython environments
try:  # MicroPython
    import urequests as _requests  # type: ignore
except Exception:  # CPython fallback
    try:
        import requests as _requests  # type: ignore
    except Exception as import_error:  # pragma: no cover
        raise RuntimeError("Neither urequests nor requests is available.") from import_error

try:
    import network  # type: ignore
    _HAS_NETWORK = True
except Exception:
    network = None  # type: ignore
    _HAS_NETWORK = False


def _urlencode_plus(query: str) -> str:
    """URL-encode a query string using + for spaces.

    Uses urllib.parse.quote_plus when available; otherwise falls back to a
    minimal encoder that is good enough for ASCII queries.
    """
    try:
        from urllib.parse import quote_plus  # type: ignore

        return quote_plus(query)
    except Exception:
        safe_chars = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-"
        )
        encoded_chars = []
        for ch in query:
            if ch == " ":
                encoded_chars.append("+")
            elif ch in safe_chars:
                encoded_chars.append(ch)
            else:
                encoded_chars.append("%{:02X}".format(ord(ch)))
        return "".join(encoded_chars)


def _http_get_json(url: str, timeout_seconds: int = 10) -> Dict[str, Any]:
    """GET a URL and return parsed JSON with robust closing and error handling.

    Works for both `urequests` and `requests`.
    """
    response = None
    try:
        # urequests may not support timeout kwarg; attempt and fallback
        try:
            response = _requests.get(url, timeout=timeout_seconds)  # type: ignore[call-arg]
        except TypeError:
            response = _requests.get(url)  # type: ignore[misc]

        status_code = getattr(response, "status_code", 200)
        if status_code and int(status_code) >= 400:
            raise RuntimeError(f"HTTP {status_code} for URL: {url}")
        return response.json()  # urequests/requests both expose .json()
    finally:
        try:
            if response is not None:
                response.close()
        except Exception:
            pass


# --- WiFi setup ---
def connect_wifi(ssid: str, password: str, timeout_seconds: int = 20) -> None:
    """Connect to Wi‑Fi on MicroPython. No-op on CPython.

    When running on MicroPython, waits up to timeout_seconds for a connection.
    """
    if not _HAS_NETWORK:
        print("Wi‑Fi connect skipped (not running on MicroPython)")
        return

    wlan = network.WLAN(network.STA_IF)  # type: ignore[attr-defined]
    wlan.active(True)

    if not ssid or ssid == "YOUR_WIFI_SSID":
        print("Wi‑Fi SSID not set. Skipping connect.")
        return

    print("Connecting to Wi‑Fi", end="")
    wlan.connect(ssid, password)

    start = time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time() * 1000)
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
        now = time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time() * 1000)
        if (now - start) >= (timeout_seconds * 1000):
            print("\nWi‑Fi connect timed out.")
            break

    if wlan.isconnected():
        try:
            print("\nConnected:", wlan.ifconfig())
        except Exception:
            print("\nConnected to Wi‑Fi.")


# --- Wikipedia summary ---
def fetch_wiki_summary(query: str) -> Tuple[str, str]:
    # Wikipedia expects underscores for spaces in titles; encode remaining
    title_path = query.strip().replace(" ", "_")
    try:
        from urllib.parse import quote  # type: ignore

        title_path = quote(title_path, safe="")
    except Exception:
        # Minimal: percent-encode only non-ASCII roughly
        title_path = "".join(
            ch if ("0" <= ch <= "9") or ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ch in "_.-" else "%{:02X}".format(ord(ch))
            for ch in title_path
        )

    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + title_path
    try:
        data = _http_get_json(url)
        return data.get("title", "No Title"), data.get("extract", "No content.")
    except Exception as exc:
        return "Error", "Could not fetch data: " + str(exc)


# --- DuckDuckGo instant answer ---
def fetch_ddg_result(query: str) -> Tuple[str, str]:
    base_url = "https://api.duckduckgo.com/"
    params = "?q=" + _urlencode_plus(query) + "&format=json&no_html=1&no_redirect=1"
    try:
        data = _http_get_json(base_url + params)
        title = data.get("Heading", "DuckDuckGo Search")
        summary = data.get("AbstractText", "")

        if not summary:
            related = data.get("RelatedTopics") or []
            if related:
                # Some entries are nested; pick first with Text if present
                first = related[0]
                if isinstance(first, dict):
                    summary = first.get("Text", "No summary.") or "No summary."
                else:
                    summary = "No summary."
            else:
                summary = "No direct answer found."

        return title, summary
    except Exception as exc:
        return "Error", "DuckDuckGo fetch failed: " + str(exc)


# --- XKCD comic fetcher ---
def fetch_xkcd(comic_number: int | None = None) -> Tuple[str, str]:
    url = f"https://xkcd.com/{comic_number}/info.0.json" if comic_number else "https://xkcd.com/info.0.json"
    try:
        data = _http_get_json(url)
        num = data.get("num", "???")
        title = data.get("title", "No title")
        alt = data.get("alt", "")
        return f"#{num} - {title}", alt
    except Exception as exc:
        return "Error", "XKCD fetch failed: " + str(exc)


# --- Hacker News top stories ---
def fetch_hn_top(n: int = 5) -> str:
    base_url = "https://hacker-news.firebaseio.com/v0"
    try:
        top_ids = _http_get_json(f"{base_url}/topstories.json")[:n]

        stories: list[str] = []
        for story_id in top_ids:
            try:
                item = _http_get_json(f"{base_url}/item/{story_id}.json")
                title = item.get("title", "No title")
                url = item.get("url", "No URL")
                stories.append(f"- {title}\n  {url}")
            except Exception:
                continue

        return "\n\n".join(stories) if stories else "No stories."
    except Exception as exc:
        return "Error fetching Hacker News: " + str(exc)


# --- Main uPB CLI loop ---
def upb_main() -> None:
    print("=== uPB v1.1 (MicroPython/CPython JSON Browser) ===")
    print("Commands: search <term>, ddg <query>, xkcd [num], hn, reload, quit\n")

    current_term = "MicroPython"

    while True:
        try:
            cmd = input("uPB> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if cmd.startswith("search "):
            current_term = cmd[7:].strip()
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
            print(
                "Unknown command. Use: search <term>, ddg <query>, xkcd [num], hn, reload, or quit."
            )
            continue

        # Default: fetch Wikipedia summary for current_term
        print("Fetching:", current_term)
        title, extract = fetch_wiki_summary(current_term)
        print("\n=== " + title + " ===")
        print(extract + "\n")


# === Wi‑Fi credentials (use secrets.py if available) ===
try:
    import secrets  # type: ignore

    WIFI_SSID = getattr(secrets, "WIFI_SSID", "YOUR_WIFI_SSID")
    WIFI_PASS = getattr(secrets, "WIFI_PASS", "YOUR_WIFI_PASSWORD")
except Exception:
    WIFI_SSID = "YOUR_WIFI_SSID"
    WIFI_PASS = "YOUR_WIFI_PASSWORD"


if __name__ == "__main__":
    # Only try Wi‑Fi on MicroPython or when explicit credentials provided
    connect_wifi(WIFI_SSID, WIFI_PASS)
    upb_main()
