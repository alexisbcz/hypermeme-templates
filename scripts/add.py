#!/usr/bin/env python3
"""Starts a template from a post on X.

    python3 scripts/add.py https://x.com/user/status/123 some-id

Downloads the post's first image into templates/<id>/ and writes a template.json with the
source filled in. Fill in name, aliases, description, usage and tags, then run build.py.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADERS = {"User-Agent": "hypermeme-templates (+https://github.com/alexisbcz/hypermeme-templates)"}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=20) as response:
        return response.read()


def main(url: str, template_id: str) -> None:
    match = re.search(r"(?:x|twitter)\.com/([^/]+)/status/(\d+)", url)
    if not match:
        sys.exit("expected a link like https://x.com/user/status/123")
    tweet = json.loads(get(f"https://api.fxtwitter.com/{match[1]}/status/{match[2]}"))["tweet"]
    photos = (tweet.get("media") or {}).get("photos") or []
    if not photos:
        sys.exit("that post has no image")
    photo = photos[0]
    extension = "png" if ".png" in photo["url"] else "jpg"

    folder = ROOT / "templates" / template_id
    if folder.exists():
        sys.exit(f"{folder.relative_to(ROOT)} already exists")
    folder.mkdir(parents=True)
    (folder / f"image.{extension}").write_bytes(get(photo["url"]))

    created = tweet["created_at"]  # e.g. "Tue Oct 27 20:34:11 +0000 2026"
    from datetime import datetime
    date = datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y").date().isoformat()
    meta = {
        "name": "", "aliases": [], "description": "", "usage": "", "tags": [],
        "image": f"image.{extension}", "width": photo["width"], "height": photo["height"],
        "captionStrip": False, "boxes": [],
        "source": {"url": tweet["url"], "author": "@" + tweet["author"]["screen_name"],
                   "date": date, "example": tweet.get("text", "")},
    }
    (folder / "template.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(f"created {folder.relative_to(ROOT)}: fill in its template.json, then run scripts/build.py")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
