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


def _http_get_json(url: str, timeout_seconds: int = 10, headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    """GET a URL and return parsed JSON with robust closing and error handling.

    Works for both `urequests` and `requests`.
    """
    response = None
    try:
        # urequests may not support timeout kwarg; attempt and fallback
        try:
            response = _requests.get(url, timeout=timeout_seconds, headers=headers)  # type: ignore[call-arg]
        except TypeError:
            # Older urequests: no timeout/headers kwarg support
            if headers:
                response = _requests.get(url, headers=headers)  # type: ignore[misc]
            else:
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


def _http_get_text(url: str, timeout_seconds: int = 10, headers: Dict[str, str] | None = None) -> str:
    """GET a URL and return text body, with robust closing and error handling."""
    response = None
    try:
        try:
            response = _requests.get(url, timeout=timeout_seconds, headers=headers)  # type: ignore[call-arg]
        except TypeError:
            if headers:
                response = _requests.get(url, headers=headers)  # type: ignore[misc]
            else:
                response = _requests.get(url)  # type: ignore[misc]

        status_code = getattr(response, "status_code", 200)
        if status_code and int(status_code) >= 400:
            raise RuntimeError(f"HTTP {status_code} for URL: {url}")
        # Try text property; fallback to content decode
        try:
            return response.text  # type: ignore[attr-defined]
        except Exception:
            try:
                content = getattr(response, "content", b"")
                if isinstance(content, bytes):
                    return content.decode("utf-8", errors="replace")
                return str(content)
            except Exception:
                return ""
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


# --- Additional APIs ---
def fetch_quote() -> Tuple[str, str]:
    """Random quote from Quotable API."""
    try:
        data = _http_get_json("https://api.quotable.io/random")
        content = data.get("content", "No quote.")
        author = data.get("author", "Unknown")
        return f"Quote by {author}", content
    except Exception as exc:
        return "Error", "Quote fetch failed: " + str(exc)


def fetch_joke() -> Tuple[str, str]:
    """Random joke from icanhazdadjoke."""
    try:
        headers = {
            "Accept": "application/json",
            "User-Agent": "uPB/1.2 (https://github.com)"
        }
        data = _http_get_json("https://icanhazdadjoke.com/", headers=headers)
        joke = data.get("joke", "No joke found.")
        return "Dad Joke", joke
    except Exception as exc:
        return "Error", "Joke fetch failed: " + str(exc)


def fetch_weather(place: str) -> Tuple[str, str]:
    """Current weather for a place using Open‑Meteo geocoding + forecast."""
    try:
        q = _urlencode_plus(place)
        geo = _http_get_json(f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=1")
        results = geo.get("results") or []
        if not results:
            return "Weather", f"No location found for '{place}'."
        r0 = results[0]
        lat = r0.get("latitude")
        lon = r0.get("longitude")
        name = r0.get("name", place)
        country = r0.get("country", "")
        forecast = _http_get_json(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        )
        cw = forecast.get("current_weather") or {}
        temp = cw.get("temperature")
        wind = cw.get("windspeed")
        code = cw.get("weathercode")
        desc = f"Temp: {temp}°C, Wind: {wind} km/h, Code: {code}"
        title = f"Weather - {name}, {country}".strip().strip(',')
        return title, desc
    except Exception as exc:
        return "Error", "Weather fetch failed: " + str(exc)


def fetch_define(word: str) -> Tuple[str, str]:
    """Dictionary definition via dictionaryapi.dev."""
    try:
        w = word.strip()
        data = _http_get_json(f"https://api.dictionaryapi.dev/api/v2/entries/en/{_urlencode_plus(w)}")
        if isinstance(data, list) and data:
            entry = data[0]
            word_out = entry.get("word", w)
            meanings = entry.get("meanings") or []
            if meanings:
                defs = meanings[0].get("definitions") or []
                if defs:
                    definition = defs[0].get("definition", "No definition.")
                    return f"Define - {word_out}", definition
        return f"Define - {w}", "No definition found."
    except Exception as exc:
        return "Error", "Definition fetch failed: " + str(exc)


_COINGECKO_IDS = {
    "btc": "bitcoin",
    "eth": "ethereum",
    "sol": "solana",
    "ada": "cardano",
    "doge": "dogecoin",
    "xrp": "ripple",
    "matic": "polygon",
}


def fetch_prices(symbols: str) -> Tuple[str, str]:
    """Simple crypto prices via CoinGecko (USD). Symbols space/comma separated."""
    try:
        tokens = [t.lower() for t in symbols.replace(",", " ").split() if t.strip()]
        if not tokens:
            tokens = ["btc", "eth"]
        ids = [(_COINGECKO_IDS.get(t) or t) for t in tokens]
        ids_param = ",".join(ids)
        data = _http_get_json(
            f"https://api.coingecko.com/api/v3/simple/price?ids={_urlencode_plus(ids_param)}&vs_currencies=usd"
        )
        lines = []
        for t, id_ in zip(tokens, ids):
            price = data.get(id_, {}).get("usd")
            if price is not None:
                lines.append(f"{t.upper()}: ${price}")
        return "Prices (USD)", "\n".join(lines) if lines else "No prices found."
    except Exception as exc:
        return "Error", "Price fetch failed: " + str(exc)


def fetch_stocks(symbols: str) -> Tuple[str, str]:
    """Stock quotes via Yahoo Finance public endpoint.

    Usage: stock AAPL MSFT TSLA
    """
    tokens = [t.upper() for t in symbols.replace(",", " ").split() if t.strip()]
    if not tokens:
        tokens = ["AAPL", "MSFT"]
    symbols_param = ",".join(tokens)
    headers = {"User-Agent": "uPB/1.2 (+https://github.com)"}

    # Try Yahoo Finance JSON first
    try:
        data = _http_get_json(
            f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={_urlencode_plus(symbols_param)}",
            headers=headers,
        )
        results = (data.get("quoteResponse") or {}).get("result") or []
        lines: list[str] = []
        for q in results:
            sym = q.get("symbol", "?")
            price = q.get("regularMarketPrice")
            change = q.get("regularMarketChange")
            percent = q.get("regularMarketChangePercent")
            currency = q.get("currency", "")
            if price is None:
                continue
            def fmt(x: Any) -> str:
                return f"{x:+.2f}" if isinstance(x, (int, float)) else "n/a"
            lines.append(f"{sym}: {price} {currency} ({fmt(change)}, {fmt(percent)}%)")
        if lines:
            return "Stocks", "\n".join(lines)
        # Fallthrough to Stooq if empty
    except Exception:
        pass

    # Fallback: Stooq CSV (no key). Fields: Symbol,Date,Time,Open,High,Low,Close,Volume,Name
    try:
        csv = _http_get_text(
            f"https://stooq.com/q/l/?s={_urlencode_plus(symbols_param)}&f=sd2t2ohlcvn&h=e",
            headers=headers,
        )
        lines_out: list[str] = []
        for idx, line in enumerate(csv.splitlines()):
            parts = [p.strip() for p in line.split(",")]
            if not parts or parts[0].lower() in ("symbol", "no data"):
                continue
            if len(parts) < 8:
                continue
            sym, _date, _time, o, h, l, c, v = parts[:8]
            if c in ("N/D", "-", ""):
                continue
            lines_out.append(f"{sym}: {c} (O:{o} H:{h} L:{l})")
        return "Stocks", "\n".join(lines_out) if lines_out else "No stock data found."
    except Exception as exc:
        return "Error", "Stock fetch failed: " + str(exc)


def fetch_time(zone: str | None = None) -> Tuple[str, str]:
    """World time via worldtimeapi.org. If zone omitted, uses IP-based zone."""
    try:
        url = (
            f"https://worldtimeapi.org/api/timezone/{zone}" if zone else "https://worldtimeapi.org/api/ip"
        )
        data = _http_get_json(url)
        dt = data.get("datetime", "")
        tz = data.get("timezone", zone or "")
        # Trim ISO string for readability
        nice = dt.replace("T", " ").split(".")[0]
        return f"Time - {tz}", nice
    except Exception as exc:
        return "Error", "Time fetch failed: " + str(exc)


def fetch_ip() -> Tuple[str, str]:
    try:
        data = _http_get_json("https://api.ipify.org?format=json")
        return "IP Address", str(data.get("ip", "Unknown"))
    except Exception as exc:
        return "Error", "IP fetch failed: " + str(exc)


def fetch_catfact() -> Tuple[str, str]:
    try:
        data = _http_get_json("https://catfact.ninja/fact")
        return "Cat Fact", data.get("fact", "No fact.")
    except Exception as exc:
        return "Error", "Cat fact fetch failed: " + str(exc)


def fetch_advice() -> Tuple[str, str]:
    try:
        data = _http_get_json("https://api.adviceslip.com/advice")
        slip = data.get("slip") or {}
        return "Advice", slip.get("advice", "No advice.")
    except Exception as exc:
        return "Error", "Advice fetch failed: " + str(exc)


# --- Main uPB CLI loop ---
def upb_main() -> None:
    print("=== uPB v1.2 (MicroPython/CPython JSON Browser) ===")
    print(
        "Commands: search <term>, ddg <query>, xkcd [num], hn, quote, joke, weather <place>, define <word>, price <symbols>, time [zone], ip, cat, advice, reload, quit\n"
    )

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
        elif cmd == "quote":
            title, text = fetch_quote()
            print("\n=== " + title + " ===")
            print(text + "\n")
            continue
        elif cmd == "joke":
            title, text = fetch_joke()
            print("\n=== " + title + " ===")
            print(text + "\n")
            continue
        elif cmd.startswith("weather "):
            place = cmd[len("weather "):].strip()
            title, text = fetch_weather(place)
            print("\n=== " + title + " ===")
            print(text + "\n")
            continue
        elif cmd.startswith("define "):
            word = cmd[len("define "):].strip()
            title, text = fetch_define(word)
            print("\n=== " + title + " ===")
            print(text + "\n")
            continue
        elif cmd.startswith("price"):
            parts = cmd.split(maxsplit=1)
            syms = parts[1] if len(parts) > 1 else "btc eth"
            title, text = fetch_prices(syms)
            print("\n=== " + title + " ===")
            print(text + "\n")
            continue
        elif cmd.startswith("stock"):
            parts = cmd.split(maxsplit=1)
            syms = parts[1] if len(parts) > 1 else "AAPL MSFT"
            title, text = fetch_stocks(syms)
            print("\n=== " + title + " ===")
            print(text + "\n")
            continue
        elif cmd.startswith("time"):
            parts = cmd.split(maxsplit=1)
            zone = parts[1] if len(parts) > 1 else None
            title, text = fetch_time(zone)
            print("\n=== " + title + " ===")
            print(text + "\n")
            continue
        elif cmd == "ip":
            title, text = fetch_ip()
            print("\n=== " + title + " ===")
            print(text + "\n")
            continue
        elif cmd == "cat":
            title, text = fetch_catfact()
            print("\n=== " + title + " ===")
            print(text + "\n")
            continue
        elif cmd == "advice":
            title, text = fetch_advice()
            print("\n=== " + title + " ===")
            print(text + "\n")
            continue
        else:
            print(
                "Unknown command. Use: search <term>, ddg <query>, xkcd [num], hn, quote, joke, weather <place>, define <word>, price <symbols>, stock <symbols>, time [zone], ip, cat, advice, reload, or quit."
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
