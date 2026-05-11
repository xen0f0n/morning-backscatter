#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from common import ROOT, DIST_DIR, load_issues, load_site_config
from generate_og import generate_og_image

TEMPLATES_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"

from urllib.parse import urlparse


def write_cname(site: dict) -> None:
    """Write GitHub Pages custom-domain CNAME file into dist/."""
    base_url = str(site.get("baseUrl", "")).strip()
    domain = urlparse(base_url).netloc or base_url
    domain = domain.replace("https://", "").replace("http://", "").strip("/")

    if domain and "localhost" not in domain:
        write_file(DIST_DIR / "CNAME", f"{domain}\n")


def clean_dist() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def copy_assets() -> None:
    if ASSETS_DIR.exists():
        shutil.copytree(ASSETS_DIR, DIST_DIR / "assets", dirs_exist_ok=True)
    (DIST_DIR / ".nojekyll").write_text("", encoding="utf-8")


def get_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build(include_drafts: bool = False, base_url: str | None = None) -> None:
    site = load_site_config(base_url)
    issues = load_issues(site, include_drafts=include_drafts)

    clean_dist()
    copy_assets()
    

    env = get_env()
    issue_template = env.get_template("issue.html.j2")
    index_template = env.get_template("index.html.j2")
    rss_template = env.get_template("rss.xml.j2")

    for issue in issues:
        generate_og_image(issue, site, DIST_DIR / "assets" / "og" / f"{issue['slug']}.png")        
        issue_json = json.dumps(issue, ensure_ascii=False)
        html = issue_template.render(site=site, issue=issue, issue_json=issue_json)
        write_file(DIST_DIR / "issue" / issue["slug"] / "index.html", html)

    latest = issues[0] if issues else None
    write_file(DIST_DIR / "index.html", index_template.render(site=site, latest=latest, issues=issues))
    write_file(DIST_DIR / "rss.xml", rss_template.render(site=site, issues=issues))
    print(f"Built {len(issues)} issue(s) into {DIST_DIR}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-drafts", action="store_true", help="Build drafts and future issues for preview.")
    parser.add_argument("--base-url", default=None, help="Override content/site.yml baseUrl, e.g. http://localhost:8000")
    args = parser.parse_args()

    build(include_drafts=args.include_drafts, base_url=args.base_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
