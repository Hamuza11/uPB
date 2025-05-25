# uPB - MicroPython JSON Browser v1.0

A tiny text-only browser for MicroPython boards with Wi-Fi (like Pico W or ESP32).

It fetches JSON from APIs like Wikipedia, DuckDuckGo, XKCD, and Hacker News, then shows it on serial.

## Features
- Wi-Fi auto-connect
- Wikipedia summary search
- DuckDuckGo instant answers
- XKCD comics (latest or specific number)
- Hacker News top stories (top 5)
- Runs on serial console, no HTML parsing

## Usage
1. Edit `main.py` with your Wi-Fi credentials.
2. Upload to your MicroPython board.
3. Open serial terminal and enjoy browsing via commands:
   - `search <term>`
   - `ddg <query>`
   - `xkcd [comic_number]`
   - `hn`
   - `reload`
   - `quit`

## License
See `LICENSE` if you really want to.

Made by Hamza, Gen Z coding legend from Oldenburg 😎
