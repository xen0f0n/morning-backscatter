#!/usr/bin/env python3
from __future__ import annotations

import base64
from pathlib import Path
from urllib.parse import urlparse

import cairosvg


ROOT = Path(__file__).resolve().parents[1]

OG_SOURCE_DIR = ROOT / "og"
TEMPLATE_PATH = OG_SOURCE_DIR / "template.svg"
CONTOURS_PATH = OG_SOURCE_DIR / "contours.png"


def normalise_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    return parsed.netloc or base_url.replace("https://", "").replace("http://", "").strip("/")


def png_to_data_uri(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing contour PNG: {path}")

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def issue_number(issue: dict) -> int:
    value = issue.get("issueNo") or issue.get("issue_no")

    if value is None:
        raise KeyError("Issue is missing 'issueNo'")

    return int(value)


def generate_og_image(issue: dict, site: dict, output_path: Path) -> None:
    """
    Generate a 1200x630 Open Graph PNG from:
    - og/template.svg
    - og/contours.png
    - issue.issueNo

    This keeps the OG template and contour artwork out of dist/,
    while writing only the final generated PNG to dist/assets/og/.
    """
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Missing OG template: {TEMPLATE_PATH}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    svg = TEMPLATE_PATH.read_text(encoding="utf-8")

    issue_no = issue_number(issue)
    # site_url = normalise_url(str(site.get("baseUrl", "https://morningbackscatter.space")))
    contour_data_uri = png_to_data_uri(CONTOURS_PATH)

    replacements = {
        "{{ISSUE}}": f"{issue_no:03d}",
        # "{{SITE_URL}}": site_url,
        "{{BYLINE}}": str(site.get("bylineName", "Spectral Reflectance")),
        "{{TAGLINE_LINE_1}}": "A quick morning overpass of the",
        "{{TAGLINE_LINE_2}}": "remote sensing and geospatial world.",
    }

    for key, value in replacements.items():
        svg = svg.replace(key, value)

    # Support both SVG href styles.
    svg = svg.replace('href="contours.png"', f'href="{contour_data_uri}"')
    svg = svg.replace("href='contours.png'", f"href='{contour_data_uri}'")
    svg = svg.replace('xlink:href="contours.png"', f'xlink:href="{contour_data_uri}"')
    svg = svg.replace("xlink:href='contours.png'", f"xlink:href='{contour_data_uri}'")

    cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        write_to=str(output_path),
        output_width=1200,
        output_height=630,
    )