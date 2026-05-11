from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from PIL import Image, ImageDraw, ImageFont

OG_SIZE = (1200, 627)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _load_background(issue: dict[str, Any]) -> Image.Image:
    url = issue.get("quicklook", {}).get("thumbUrl") or issue.get("quicklook", {}).get("fullUrl")
    if url and urlparse(str(url)).scheme in {"http", "https"}:
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")
        except Exception:
            pass
    return Image.new("RGB", OG_SIZE, (10, 12, 18))


def _cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    img = img.convert("RGB")
    src_w, src_h = img.size
    dst_w, dst_h = size
    scale = max(dst_w / src_w, dst_h / src_h)
    resized = img.resize((int(src_w * scale), int(src_h * scale)))
    left = (resized.width - dst_w) // 2
    top = (resized.height - dst_h) // 2
    return resized.crop((left, top, left + dst_w, top + dst_h))


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_og_image(issue: dict[str, Any], site: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bg = _cover(_load_background(issue), OG_SIZE)
    overlay = Image.new("RGB", OG_SIZE, (5, 8, 12))
    img = Image.blend(bg, overlay, 0.48)
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((58, 58, 1142, 569), radius=34, fill=(0, 0, 0), outline=(255, 255, 255), width=2)

    title_font = _font(72, bold=True)
    issue_font = _font(30, bold=True)
    label_font = _font(24, bold=True)
    text_font = _font(28, bold=False)
    small_font = _font(22, bold=False)

    draw.text((92, 92), site.get("title", "The Morning Backscatter"), font=title_font, fill=(255, 255, 255))
    draw.text((98, 180), f"Issue #{int(issue['issueNo']):03d}", font=issue_font, fill=(110, 231, 183))
    draw.text((98, 246), "PULSE  ·  QUICKLOOK  ·  COHERENCE  ·  DOUBLE BOUNCE", font=label_font, fill=(196, 181, 253))

    y = 318
    for line in _wrap_text(draw, issue.get("tagline") or site.get("tagline", ""), text_font, 860)[:2]:
        draw.text((98, y), line, font=text_font, fill=(235, 245, 255))
        y += 42

    pulse_title = issue.get("pulse", {}).get("title", "")
    if pulse_title:
        y += 16
        draw.text((98, y), "Today's pulse:", font=small_font, fill=(251, 146, 60))
        y += 34
        for line in _wrap_text(draw, pulse_title, text_font, 820)[:2]:
            draw.text((98, y), line, font=text_font, fill=(255, 255, 255))
            y += 40

    draw.text((98, 522), site.get("bylineName", "Spectral Reflectance"), font=small_font, fill=(180, 190, 205))
    draw.text((884, 522), "morning-backscatter", font=small_font, fill=(180, 190, 205))
    img.save(output_path, "PNG")
