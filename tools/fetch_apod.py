"""Fetch and cache today's NASA Astronomy Picture of the Day.

Run once with internet::

    python tools/fetch_apod.py

Writes ``data/cache/apod.json`` and ``data/cache/apod.jpg``. The game never needs the
network afterwards: without this file it shows the bundled offline entry.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
APOD_JSON = CACHE / "apod.json"
APOD_IMAGE = CACHE / "apod.jpg"

API = "https://api.nasa.gov/planetary/apod?api_key={key}&thumbs=True"
# A demo key is fine for a one-off fetch; swap in your own key if you have one.
DEFAULT_KEY = "DEMO_KEY"


def fetch(key: str = DEFAULT_KEY) -> bool:
    CACHE.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        API.format(key=key),
        headers={"User-Agent": "Homebound-SpaceApp/1.0 (pygame game; contact: imamsanghaar@gmail.com)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        print(f"APOD fetch failed: {exc}")
        return False

    payload = {
        "title": data.get("title", "NASA APOD"),
        "explanation": data.get("explanation", ""),
        "url": data.get("url", ""),
        "hdurl": data.get("hdurl", ""),
        "media_type": data.get("media_type", "image"),
        "date": data.get("date", ""),
        "fetched_at": data.get("date", ""),
        "offline_fallback": False,
    }

    image_url = data.get("thumbnail_url") or data.get("url", "")
    if data.get("media_type") == "image" and image_url:
        try:
            image_request = urllib.request.Request(image_url, headers={"User-Agent": "Homebound-SpaceApp/1.0"})
            with urllib.request.urlopen(image_request, timeout=30) as response:
                image_bytes = response.read()
            APOD_IMAGE.write_bytes(image_bytes)
        except OSError as exc:
            print(f"APOD image download failed (text card will be used): {exc}")

    APOD_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"APOD cached: {payload['title']}")
    return True


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_KEY
    raise SystemExit(0 if fetch(key) else 1)
