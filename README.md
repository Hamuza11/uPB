# uPB - MicroPython/CPython JSON Browser v1.1

A tiny text-only browser for MicroPython boards with Wi‑Fi (like Pico W or ESP32) and now also runnable on desktop CPython for quick testing.

It fetches JSON from APIs like Wikipedia, DuckDuckGo, XKCD, and Hacker News, then shows it on serial/terminal.

## Features
- Wi‑Fi auto-connect on MicroPython
- Wikipedia summary search
- DuckDuckGo instant answers
- XKCD comics (latest or specific number)
- Hacker News top stories (top 5)
- Runs on serial console/terminal, no HTML parsing

## Quick start (desktop / CPython)
1. Optional: create and activate a virtualenv.
2. Install dependency:
   ```bash
   pip install requests
   ```
3. Run:
   ```bash
   python main.py
   ```

## Quick start (MicroPython)
1. Create a `secrets.py` with your Wi‑Fi credentials (see below), or edit constants in `main.py` directly.
2. Upload `main.py` (and `secrets.py` if used) to your MicroPython board.
3. Open a serial terminal and use commands below.

## Commands
- `search <term>`
- `ddg <query>`
- `xkcd [comic_number]`
- `hn`
- `reload`
- `quit`

## Wi‑Fi credentials via secrets.py
Create a `secrets.py` file alongside `main.py` with:
```python
WIFI_SSID = "your-ssid"
WIFI_PASS = "your-password"
```
This keeps credentials out of version control and lets you run the same code on both MicroPython and CPython.

## License
See `LICENSE`.

Made by Hamza. Polished for reliability and portability. 😎
