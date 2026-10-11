# omnist-web

Static site for [omnist.dev](https://omnist.dev), served directly from  by GitHub Pages.

## Port versions are updated automatically

The Implementations table in  shows each port's current version.
Nobody edits those cells by hand.  reads the live registries
(PyPI, npm, crates.io, the Go module proxy, Maven Central) and rewrites only the
version cells between the  /  comments.

- The  workflow runs daily (and on manual ), runs
  , and if anything changed commits it to  as
  . No PR is involved. No change means no commit.
- On every push to  the workflow runs  instead,
  which fails if the page disagrees with the registries. It never writes, so the
  bot's own commit cannot trigger another one.
- If a registry is unreachable or unparseable, that row keeps its committed
  value and a warning is logged. A registry value lower than the committed one
  is never applied.

Run it locally with  or  (stdlib only).
