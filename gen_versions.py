#!/usr/bin/env python3
"""Keeps index.html's Implementations table in sync with the live registries.

The version cell of each port row, between the <!-- versions:begin --> and
<!-- versions:end --> markers, is the only thing this script touches. The
registries (PyPI, npm, crates.io, the Go module proxy, Maven Central) are the
source of truth -- not a git tag, since a tagged release can lag its real
publish.

  gen_versions.py --check   exit 1 if the page differs from the registries
  gen_versions.py --write   rewrite the version cells in place

A registry that is unreachable or unparseable is skipped with a warning and
that row keeps its committed value. A registry value is only taken if it is
>= the committed one, so a flaky or stale mirror can never downgrade the page.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request

INDEX_HTML = "index.html"
BEGIN = "<!-- versions:begin -->"
END = "<!-- versions:end -->"
UA = "omnist-web-gen-versions"


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def fetch_json(url: str) -> object:
    return json.loads(fetch_text(url))


SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$")


def semver_key(v: str):
    """Sort key per semver precedence; raises ValueError if not semver."""
    m = SEMVER.match(v)
    if not m:
        raise ValueError(f"not a semver version: {v!r}")
    core = tuple(int(x) for x in m.group(1, 2, 3))
    if m.group(4) is None:
        return (core, 1, ())  # a release outranks its own prereleases
    ids = tuple((0, int(i), "") if i.isdigit() else (1, 0, i) for i in m.group(4).split("."))
    return (core, 0, ids)


def live_python() -> str:
    return fetch_json("https://pypi.org/pypi/omnist/json")["info"]["version"]  # type: ignore[index]


def live_typescript() -> str:
    return fetch_json("https://registry.npmjs.org/@omnist-dev/omnist")["dist-tags"]["latest"]  # type: ignore[index]


def live_rust() -> str:
    return fetch_json("https://crates.io/api/v1/crates/omnist")["crate"]["max_version"]  # type: ignore[index]


def live_go() -> str:
    # Module proxy, not the rate-limited GitHub tags API.
    tags = fetch_text("https://proxy.golang.org/github.com/omnist-dev/omnist-go/@v/list").split()
    good = [t for t in tags if SEMVER.match(t)]
    if not good:
        raise ValueError("no semver tags from the Go module proxy")
    return max(good, key=semver_key).lstrip("v")


def live_java() -> str:
    xml = fetch_text("https://repo1.maven.org/maven2/dev/omnist/omnist-j/maven-metadata.xml")
    m = re.search(r"<latest>([^<]+)</latest>", xml) or re.search(r"<release>([^<]+)</release>", xml)
    if not m:
        raise ValueError("maven-metadata.xml has no <latest>/<release> tag")
    return m.group(1)


# (display name as in index.html's <a> text, live-version fetcher)
PORTS = [
    ("Python", live_python),
    ("TypeScript", live_typescript),
    ("Rust", live_rust),
    ("Go", live_go),
    ("Java", live_java),
]

ROW = re.compile(r'(<tr><td><a href="[^"]+">)([^<]+)(</a></td><td>)([^<]+)(</td>)')


def compute(html: str) -> tuple[str, list[str]]:
    """Returns (new html, drift messages). Warnings go to stderr."""
    b, e = html.find(BEGIN), html.find(END)
    if b < 0 or e < b:
        raise SystemExit(f"{INDEX_HTML}: version markers missing")
    head, block, tail = html[: b + len(BEGIN)], html[b + len(BEGIN) : e], html[e:]
    live: dict[str, str] = {}
    for name, fetch in PORTS:
        try:
            v = fetch()
            semver_key(v)
            live[name] = v
        except Exception as ex:  # noqa: BLE001 -- best effort against 5 external services
            print(f"warning: {name}: registry unavailable, keeping committed value ({ex})", file=sys.stderr)
    drift: list[str] = []
    seen: set[str] = set()

    def sub(m: re.Match) -> str:
        name, old = m.group(2), m.group(4)
        seen.add(name)
        new = live.get(name)
        if new is None or new == old:
            return m.group(0)
        try:
            ok = semver_key(new) >= semver_key(old)
        except ValueError:
            ok = True  # committed value not semver; trust the registry
        if not ok:
            print(f"warning: {name}: registry {new} is lower than committed {old}, keeping committed", file=sys.stderr)
            drift.append(f"{name}: page {old}, registry {new} (lower; not applied)")
            return m.group(0)
        drift.append(f"{name}: page {old}, registry {new}")
        return m.group(1) + name + m.group(3) + new + m.group(5)

    block = ROW.sub(sub, block)
    for name, _ in PORTS:
        if name not in seen:
            raise SystemExit(f"{name}: row not found between the version markers in {INDEX_HTML}")
    return head + block + tail, drift


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in ("--check", "--write"):
        print(__doc__, file=sys.stderr)
        return 2
    with open(INDEX_HTML, encoding="utf-8", newline="") as f:
        html = f.read()
    new, drift = compute(html)
    if argv[1] == "--check":
        if drift:
            print("index.html is out of sync with the registries:", file=sys.stderr)
            for d in drift:
                print(f"  - {d}", file=sys.stderr)
            return 1
        print("Every port's displayed version matches its registry.")
        return 0
    if new != html:
        with open(INDEX_HTML, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        for d in drift:
            print(f"updated {d}")
    else:
        print("No changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
