#!/usr/bin/env python3
from __future__ import annotations

import base64
from pathlib import Path

import cairosvg


ROOT = Path(__file__).resolve().parents[1]

OG_SOURCE_DIR = ROOT / "og"
TEMPLATE_PATH = OG_SOURCE_DIR / "template.svg"
CONTOURS_PATH = OG_SOURCE_DIR / "contours.png"


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


def issue_block(issue_no: int) -> str:
    return f'''
  <line x1="80" y1="405" x2="125" y2="405" stroke="#10a8d8" stroke-width="4"/>
  <text x="150" y="415" font-size="28" font-family="Inter, Arial, sans-serif" font-weight="700" fill="#10a8d8">Issue #{issue_no:03d}</text>
'''


def render_og_svg(*, issue_no: int | None = None) -> str:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Missing OG template: {TEMPLATE_PATH}")

    svg = TEMPLATE_PATH.read_text(encoding="utf-8")
    contour_data_uri = png_to_data_uri(CONTOURS_PATH)

    replacements = {
        "{{ISSUE_BLOCK}}": issue_block(issue_no) if issue_no is not None else "",
        "{{TAGLINE_LINE_1}}": "A quick morning overpass of the",
        "{{TAGLINE_LINE_2}}": "remote sensing and geospatial world.",
        "{{BYLINE}}": "Spectral Reflectance",
        "{{SITE_URL}}": "morningbackscatter.space",
    }

    for key, value in replacements.items():
        svg = svg.replace(key, value)

    svg = svg.replace('href="contours.png"', f'href="{contour_data_uri}"')
    svg = svg.replace("href='contours.png'", f"href='{contour_data_uri}'")
    svg = svg.replace('xlink:href="contours.png"', f'xlink:href="{contour_data_uri}"')
    svg = svg.replace("xlink:href='contours.png'", f"xlink:href='{contour_data_uri}'")

    return svg


def render_svg_to_png(svg: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        write_to=str(output_path),
        output_width=1200,
        output_height=630,
    )


def generate_og_image(issue: dict, site: dict, output_path: Path) -> None:
    svg = render_og_svg(issue_no=issue_number(issue))
    render_svg_to_png(svg, output_path)


def generate_home_og_image(site: dict, output_path: Path) -> None:
    svg = render_og_svg(issue_no=None)
    render_svg_to_png(svg, output_path)