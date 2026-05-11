from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
ISSUES_DIR = CONTENT_DIR / "issues"
DIST_DIR = ROOT / "dist"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def load_site_config(base_url_override: str | None = None) -> dict[str, Any]:
    site = load_yaml(CONTENT_DIR / "site.yml")
    if base_url_override:
        site["baseUrl"] = base_url_override.rstrip("/")
    else:
        site["baseUrl"] = str(site.get("baseUrl", "")).rstrip("/")
    return site


def parse_dt(value: str) -> datetime:
    if not value:
        raise ValueError("Missing datetime value")
    value = str(value).replace("Z", "+00:00")
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError(f"Datetime must include timezone: {value}")
    return dt


def is_url(value: str) -> bool:
    try:
        parsed = urlparse(str(value))
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def absolute_url(site: dict[str, Any], value: str | None) -> str:
    if not value:
        return ""
    value = str(value)
    if is_url(value):
        return value
    return urljoin(site["baseUrl"] + "/", value.lstrip("/"))


def load_issues(site: dict[str, Any], include_drafts: bool = False) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    issues: list[dict[str, Any]] = []

    for path in sorted(ISSUES_DIR.glob("*.yml")):
        issue = load_yaml(path)
        issue["_source"] = str(path.relative_to(ROOT))

        status = issue.get("status", "draft")
        publish_at = parse_dt(issue["publishAt"])

        if not include_drafts:
            if status != "ready":
                continue
            if publish_at.astimezone(timezone.utc) > now:
                continue

        issue["dateISO"] = publish_at.date().isoformat()
        issue["canonicalUrl"] = f"{site['baseUrl']}/issue/{issue['slug']}/"
        issue["ogImageUrl"] = f"{site['baseUrl']}/assets/og/{issue['slug']}.png"
        issue["path"] = f"{site['baseUrl']}/issue/{issue['slug']}/"
        issue["rssDate"] = publish_at.strftime("%a, %d %b %Y %H:%M:%S %z")

        issue["bylineName"] = issue.get("bylineName", site.get("bylineName", ""))
        issue["bylineUrl"] = issue.get("bylineUrl", site.get("bylineUrl", ""))
        issue["footer"] = issue.get("footer", site.get("footer", {}))
        issue["title"] = issue.get("title", site.get("title", "The Morning Backscatter"))
        issue["tagline"] = issue.get("tagline", site.get("tagline", ""))

        for section in ("quicklook", "promo", "doubleBounce"):
            if section in issue and isinstance(issue[section], dict):
                for key in ("thumbUrl", "fullUrl", "imgUrl", "imageUrl", "openUrl"):
                    if key in issue[section]:
                        issue[section][key] = absolute_url(site, issue[section][key])

        issues.append(issue)

    return sorted(issues, key=lambda x: int(x["issueNo"]), reverse=True)


def latest_publishable_issue(site: dict[str, Any]) -> dict[str, Any] | None:
    issues = load_issues(site, include_drafts=False)
    return issues[0] if issues else None
