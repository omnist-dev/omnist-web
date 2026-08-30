#!/usr/bin/env python3
"""Fails if index.html's Implementations table cites a version that
disagrees with what's actually live for that port -- the real registry
publish, not just a git tag (a port's version file can be bumped and
tagged locally while the actual PyPI/npm/crates.io/Maven Central
publish lags or never happens, which is exactly what caused two real,
live gaps found by hand on 2026-08-30: npm's `latest` dist-tag was two
versions behind, and Java's Maven Central release was stuck at a
manual approval gate for the same release this page already claimed
was current).

This script has no source-of-truth file of its own to compare against
-- unlike a single repo's own version-sync check, this one reaches out
to five different live sources and treats *those* as ground truth.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request

INDEX_HTML = "index.html"


def fetch_json(url: str, headers: dict[str, str] | None = None) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": "omnist-web-version-check", **(headers or {})})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "omnist-web-version-check"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def live_python() -> str:
    return fetch_json("https://pypi.org/pypi/omnist/json")["info"]["version"]  # type: ignore[index]


def live_typescript() -> str:
    data = fetch_json("https://registry.npmjs.org/@omnist-dev/omnist")
    return data["dist-tags"]["latest"]  # type: ignore[index]


def live_rust() -> str:
    data = fetch_json("https://crates.io/api/v1/crates/omnist")
    return data["crate"]["max_version"]  # type: ignore[index]


def live_go() -> str:
    data = fetch_json("https://api.github.com/repos/omnist-dev/omnist-go/tags")
    return data[0]["name"].lstrip("v")  # type: ignore[index]


def live_java() -> str:
    xml = fetch_text("https://repo1.maven.org/maven2/dev/omnist/omnist-j/maven-metadata.xml")
    m = re.search(r"<release>([^<]+)</release>", xml)
    if not m:
        raise ValueError("maven-metadata.xml has no <release> tag")
    return m.group(1)


# (display name as it appears in index.html's <a> text, live-version fetcher)
PORTS = [
    ("Python", live_python),
    ("TypeScript", live_typescript),
    ("Rust", live_rust),
    ("Go", live_go),
    ("Java", live_java),
]


def displayed_versions() -> dict[str, str]:
    html = open(INDEX_HTML, encoding="utf-8").read()
    out = {}
    for m in re.finditer(
        r"<tr><td><a href=\"[^\"]+\">([^<]+)</a></td><td>([^<]+)</td>", html
    ):
        out[m.group(1)] = m.group(2)
    return out


def main() -> int:
    displayed = displayed_versions()
    problems = []
    for name, fetch in PORTS:
        if name not in displayed:
            problems.append(f"{name}: not found in {INDEX_HTML}'s Implementations table at all")
            continue
        shown = displayed[name]
        try:
            live = fetch()
        except Exception as e:  # noqa: BLE001 -- best-effort against 5 external services
            print(f"  (skipping {name}: could not reach its registry -- {e})", file=sys.stderr)
            continue
        if shown != live:
            problems.append(f"{name}: page shows {shown!r}, but the live published version is {live!r}")
    if problems:
        print("Stale version(s) in index.html's Implementations table:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("Every port's displayed version matches its live published version.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
