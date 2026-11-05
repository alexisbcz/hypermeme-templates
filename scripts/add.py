#!/usr/bin/env python3
"""Starts a template from a post on X.

    python3 scripts/add.py https://x.com/user/status/123 some-id
    python3 scripts/add.py https://x.com/user/status/123 some-id --start 4 --length 20

Downloads the post's first image into templates/<id>/ and writes a template.json with the
source filled in. Fill in name, aliases, description, usage and tags, then run build.py.

A post with a video and no image becomes a video template: the video is cut to --start and
--length (seconds) when given, made small enough to share with ffmpeg, and its first second
becomes the poster image.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADERS = {"User-Agent": "hypermeme-templates (+https://github.com/alexisbcz/hypermeme-templates)"}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=20) as response:
        return response.read()


def add_video(video: dict, folder: Path, start: float, length: float | None) -> dict:
    """Writes video.mp4 and its poster, image.jpg, and returns their fields for template.json."""
    with tempfile.TemporaryDirectory() as scratch:
        original = Path(scratch) / "original.mp4"
        original.write_bytes(get(video["url"]))
        cut = ["-ss", str(start)] + (["-t", str(length)] if length else [])
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", *cut, "-i", str(original),
                        "-vf", "scale='min(720,iw)':-2", "-c:v", "libx264", "-crf", "26", "-preset", "slow",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
                        str(folder / "video.mp4")], check=True)
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", "1", "-i", str(folder / "video.mp4"),
                    "-frames:v", "1", "-q:v", "3", str(folder / "image.jpg")], check=True)
    probe = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
         "-of", "json", str(folder / "video.mp4")], check=True, capture_output=True, text=True).stdout)
    stream = probe["streams"][0]
    return {"image": "image.jpg", "width": stream["width"], "height": stream["height"],
            "video": "video.mp4", "duration": round(float(probe["format"]["duration"]), 1)}


def main(url: str, template_id: str, start: float = 0, length: float | None = None) -> None:
    match = re.search(r"(?:x|twitter)\.com/([^/]+)/status/(\d+)", url)
    if not match:
        sys.exit("expected a link like https://x.com/user/status/123")
    tweet = json.loads(get(f"https://api.fxtwitter.com/{match[1]}/status/{match[2]}"))["tweet"]
    photos = (tweet.get("media") or {}).get("photos") or []
    videos = (tweet.get("media") or {}).get("videos") or []
    if not photos and not videos:
        sys.exit("that post has no image or video")

    folder = ROOT / "templates" / template_id
    if folder.exists():
        sys.exit(f"{folder.relative_to(ROOT)} already exists")
    folder.mkdir(parents=True)
    if photos:
        photo = photos[0]
        extension = "png" if ".png" in photo["url"] else "jpg"
        (folder / f"image.{extension}").write_bytes(get(photo["url"]))
        media = {"image": f"image.{extension}", "width": photo["width"], "height": photo["height"]}
    else:
        media = add_video(videos[0], folder, start, length)

    created = tweet["created_at"]  # e.g. "Tue Oct 27 20:34:11 +0000 2026"
    from datetime import datetime
    date = datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y").date().isoformat()
    meta = {
        "name": "", "aliases": [], "description": "", "usage": "", "tags": [],
        **{k: v for k, v in media.items() if k in ("image", "width", "height")},
        "captionStrip": False, "boxes": [],
        **{k: v for k, v in media.items() if k in ("video", "duration")},
        "source": {"url": tweet["url"], "author": "@" + tweet["author"]["screen_name"],
                   "date": date, "example": tweet.get("text", "")},
    }
    (folder / "template.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    print(f"created {folder.relative_to(ROOT)}: fill in its template.json, then run scripts/build.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("url")
    parser.add_argument("id")
    parser.add_argument("--start", type=float, default=0, help="where a video starts, in seconds")
    parser.add_argument("--length", type=float, help="how long a video lasts, in seconds")
    args = parser.parse_args()
    main(args.url, args.id, args.start, args.length)
