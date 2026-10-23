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
