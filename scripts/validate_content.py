#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from common import ISSUES_DIR, load_yaml, parse_dt

ALLOWED_STATUS = {"draft", "ready", "archived"}
REQUIRED_TOP = ["issueNo", "slug", "status", "publishAt", "pulse", "quicklook", "coherence", "doubleBounce"]
REQUIRED_SECTIONS = {
    "pulse": ["title", "summary", "sourceUrl", "cta"],
    "quicklook": ["title", "thumbUrl", "alt", "caption", "sourceUrl", "sourceLabel"],
    "coherence": ["title", "summary", "url", "cta"],
    "doubleBounce": ["title", "caption"],
}
LIMITS = {
    ("pulse", "summary"): 300,
    ("quicklook", "caption"): 360,
    ("coherence", "summary"): 360,
    ("doubleBounce", "caption"): 220,
}


def is_http_url(value: str) -> bool:
    parsed = urlparse(str(value))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_tags(path: Path, issue: dict) -> list[str]:
    errors = []

    for section in ("pulse", "quicklook", "coherence", "doubleBounce"):
        tags = issue.get(section, {}).get("tags", [])

        if tags is None:
            continue

        if not isinstance(tags, list):
            errors.append(f"{path}: '{section}.tags' must be a list")
            continue

        for tag in tags:
            if not isinstance(tag, str):
                errors.append(f"{path}: '{section}.tags' values must be strings")
            elif " " in tag:
                errors.append(f"{path}: tag '{tag}' in '{section}.tags' should use hyphens, not spaces")

    return errors


def validate_issue(path: Path) -> list[str]:
    errors: list[str] = []
    issue = load_yaml(path)

    for key in REQUIRED_TOP:
        if key not in issue:
            errors.append(f"{path}: missing top-level key '{key}'")
    if errors:
        return errors

    if issue["status"] not in ALLOWED_STATUS:
        errors.append(f"{path}: status must be one of {sorted(ALLOWED_STATUS)}")

    try:
        parse_dt(issue["publishAt"])
    except Exception as exc:
        errors.append(f"{path}: invalid publishAt: {exc}")

    for section, keys in REQUIRED_SECTIONS.items():
        data = issue.get(section)
        if not isinstance(data, dict):
            errors.append(f"{path}: '{section}' must be a mapping")
            continue
        for key in keys:
            if not data.get(key):
                errors.append(f"{path}: missing '{section}.{key}'")

    for (section, key), max_len in LIMITS.items():
        value = str(issue.get(section, {}).get(key, ""))
        if len(value) > max_len:
            errors.append(f"{path}: '{section}.{key}' is {len(value)} chars; max is {max_len}")

    for section, key in [
        ("pulse", "sourceUrl"),
        ("quicklook", "sourceUrl"),
        ("coherence", "url"),
        ("doubleBounce", "sourceUrl"),
    ]:
        value = issue.get(section, {}).get(key)
        if value and not is_http_url(value):
            errors.append(f"{path}: '{section}.{key}' must be an http(s) URL")

    errors.extend(validate_tags(path, issue))

    return errors


def main() -> int:
    paths = sorted(ISSUES_DIR.glob("*.yml"))
    if not paths:
        print("No issue files found.")
        return 1

    all_errors: list[str] = []
    for path in paths:
        all_errors.extend(validate_issue(path))

    if all_errors:
        print("Content validation failed:")
        for err in all_errors:
            print(f" - {err}")
        return 1

    print(f"Validated {len(paths)} issue file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
