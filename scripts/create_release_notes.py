#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import latest_publishable_issue, load_site_config


def release_notes(issue: dict) -> str:
    issue_no = int(issue["issueNo"])
    return f"""# The Morning Backscatter #{issue_no:03d}

**Pulse**  
{issue["pulse"]["title"]}  
{issue["pulse"].get("summary", "")}

**Quicklook**  
{issue["quicklook"]["title"]}  
[Open quicklook]({issue["canonicalUrl"]}#quicklook)

**Coherence**  
{issue["coherence"]["title"]}  
[Read]({issue["coherence"]["url"]})

**Double Bounce**  
{issue["doubleBounce"]["title"]} - {issue["doubleBounce"].get("caption", "")}

[Open the full issue]({issue["canonicalUrl"]})
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--notes-file", default="release-notes.md")
    parser.add_argument("--github-output", default=None, help="Path to $GITHUB_OUTPUT")
    args = parser.parse_args()

    site = load_site_config(args.base_url)
    issue = latest_publishable_issue(site)

    if not issue:
        print("No publishable issue found.")
        if args.github_output:
            Path(args.github_output).write_text("has_issue=false\n", encoding="utf-8")
        return 0

    Path(args.notes_file).write_text(release_notes(issue), encoding="utf-8")

    tag = f"mb-{issue['slug']}"
    title = f"The Morning Backscatter #{int(issue['issueNo']):03d}"

    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as f:
            f.write("has_issue=true\n")
            f.write(f"issue_no={int(issue['issueNo']):03d}\n")
            f.write(f"slug={issue['slug']}\n")
            f.write(f"tag={tag}\n")
            f.write(f"title={title}\n")
            f.write(f"url={issue['canonicalUrl']}\n")

    print(f"Prepared release notes for {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
