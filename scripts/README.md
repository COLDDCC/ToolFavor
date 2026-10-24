# Localized pages

English HTML is the source. After editing the shared catalog or core pages, run:

```sh
python scripts/build-ja.py
python scripts/build-zh.py
```

Descriptions are matched to catalog order. Each build rejects a description count
that differs from the English catalog, so newly added entries must be translated.
The Chinese builder updates language navigation and alternate links across all
three published languages. English articles that have no localized version are
explicitly labeled as English in the directory.

## Tool detail pages

Tool detail pages (`/tools/*.html`, `/ja/tools/*.html`, `/zh-cn/tools/*.html`) are
no longer translated from the English HTML. Each one is generated for all three
languages from `data/tools/<slug>.json`:

```sh
python3 scripts/build-tool-pages.py --check   # validate against the tier rules
python3 scripts/build-tool-pages.py           # write pages and update sitemap lastmod
```

The content standard, tiers and the 100-point checklist are in
`docs/detail-page-standard.md`. Edit the JSON, never the generated HTML.
