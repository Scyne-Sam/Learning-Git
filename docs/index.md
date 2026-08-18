# Learning Git

Welcome to the Learning Git site. These pages are written in Markdown under `docs/`
and published automatically to GitHub Pages.

## Getting started locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-docs.txt
mkdocs serve
```

Then open <http://127.0.0.1:8000>.

## Adding a page

1. Create a new Markdown file in `docs/`.
2. Add it to the `nav` section of `mkdocs.yml`.
3. Commit and push to `main` — the site rebuilds and deploys itself.

## Quality gates

Commits are checked by [pre-commit](validation.md) before they land, and the site is
only deployed once those same checks pass in CI. If something trips, the
[failure examples](failures.md) page explains the output and the fix.
