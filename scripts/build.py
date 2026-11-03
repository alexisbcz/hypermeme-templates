#!/usr/bin/env python3
"""Checks every templates/<id>/template.json and writes index.json.

    python3 scripts/build.py          # rebuild index.json
    python3 scripts/build.py --check  # fail if index.json is out of date (CI)
"""
import json
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
INDEX = ROOT / "index.json"
RAW = "https://raw.githubusercontent.com/alexisbcz/hypermeme-templates/main/templates"

REQUIRED = {"name": str, "aliases": list, "description": str, "usage": str, "tags": list,
            "image": str, "width": int, "height": int, "captionStrip": bool, "boxes": list, "source": dict}
BOX_FIELDS = {"x", "y", "width", "height", "rotation", "font", "color", "outline",
              "allCaps", "align", "verticalAlign", "shadow", "maxFontSize"}


def image_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data):
            marker, length = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + length
    raise ValueError("not a PNG, GIF or JPEG")


def check(folder: Path) -> tuple[dict, list[str]]:
    errors = []
    meta = json.loads((folder / "template.json").read_text())
    for key, kind in REQUIRED.items():
        if not isinstance(meta.get(key), kind):
            errors.append(f"{key} should be a {kind.__name__}")
    if errors:
        return meta, errors
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", folder.name):
        errors.append("folder name should be lowercase-with-dashes")
    if not meta["description"].strip() or not meta["usage"].strip():
        errors.append("description and usage can't be empty")
    if not meta["source"].get("url"):
        errors.append("source.url is required")
    image = folder / meta["image"]
    if not image.is_file():
        errors.append(f"{meta['image']} is missing")
    else:
        try:
            size = image_size(image)
            if size != (meta["width"], meta["height"]):
                errors.append(f"width/height say {meta['width']}x{meta['height']}, image is {size[0]}x{size[1]}")
        except ValueError as e:
            errors.append(f"{meta['image']}: {e}")
    for n, box in enumerate(meta["boxes"]):
        if unknown := set(box) - BOX_FIELDS:
            errors.append(f"boxes[{n}] has unknown fields {sorted(unknown)}")
        for key in ("x", "y", "width", "height"):
            if not 0 <= box.get(key, -1) <= 1:
                errors.append(f"boxes[{n}].{key} should be a fraction between 0 and 1")
    return meta, errors


def build() -> str:
    entries, failed = [], False
    for folder in sorted(p for p in TEMPLATES.iterdir() if p.is_dir()):
        meta, errors = check(folder)
        for error in errors:
            print(f"{folder.name}: {error}", file=sys.stderr)
        failed |= bool(errors)
        entries.append({"id": folder.name, **meta, "imageURL": f"{RAW}/{folder.name}/{meta.get('image')}"})
    if failed:
        sys.exit(1)
    return json.dumps({"version": 1, "templates": entries}, indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    index = build()
    if "--check" in sys.argv:
        if not INDEX.exists() or INDEX.read_text() != index:
            sys.exit("index.json is out of date: run python3 scripts/build.py")
        print("index.json is up to date")
    else:
        INDEX.write_text(index)
        print(f"wrote {INDEX.name} with {len(json.loads(index)['templates'])} templates")
