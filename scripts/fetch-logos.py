"""Download every logo and product image used by the tool pages into this repo.

    python3 scripts/fetch-logos.py            # fetch anything not yet stored
    python3 scripts/fetch-logos.py --refresh  # re-download everything

Runs automatically in GitHub Actions (.github/workflows/fetch-logos.yml) whenever
data/tools/*.json changes, then rebuilds the pages so they point at /assets/...

How a logo is chosen
  1. `logo` in the tool's JSON (an image URL, or a file already in /assets).
  2. `app_store_id` in the JSON: the 512 px App Store icon via Apple's lookup API.
  3. Otherwise the site's own icons: apple-touch-icon / manifest icons / Google's
     favicon service, keeping whichever is largest.
Files go to assets/logos/ and assets/media/, and data/assets.json maps each remote
URL to its local copy. Failures are reported but never break the build: the page
simply keeps using the remote URL until the next successful run.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urljoin
from datetime import date
from io import BytesIO
import hashlib, importlib.util, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts' / 'build-tool-pages.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

UA = 'Mozilla/5.0 (compatible; ToolFavorAssetBot/1.0; +https://toolfavor.com/contact)'
TYPES = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/gif': 'gif', 'image/webp': 'webp',
         'image/svg+xml': 'svg', 'image/x-icon': 'ico', 'image/vnd.microsoft.icon': 'ico', 'image/avif': 'avif'}
MAX_BYTES = {'logo': 3_000_000, 'favicon': 1_000_000, 'media': 12_000_000}
MIN_HERO_LOGO = 256


def get(url, limit):
    req = Request(url, headers={'User-Agent': UA, 'Accept': 'image/*,text/html;q=0.8,*/*;q=0.5'})
    with urlopen(req, timeout=20) as r:
        data = r.read(limit + 1)
        if len(data) > limit:
            raise ValueError(f'larger than {limit} bytes')
        return r.headers.get_content_type(), data, r.geturl()


def sniff(ctype, data):
    if ctype in TYPES:
        return TYPES[ctype]
    head = data[:16]
    if head.startswith(b'\x89PNG'): return 'png'
    if head[:3] == b'\xff\xd8\xff': return 'jpg'
    if head[:4] == b'GIF8': return 'gif'
    if head[:4] == b'RIFF' and data[8:12] == b'WEBP': return 'webp'
    if b'<svg' in data[:500].lower(): return 'svg'
    return None


def pixel_size(data, ext):
    if ext == 'svg':
        return (10_000, 10_000)  # vector: always sharp
    try:
        from PIL import Image
        with Image.open(BytesIO(data)) as im:
            if ext == 'ico':
                return max(im.info.get('sizes', [im.size]))
            return im.size
    except Exception:
        return (0, 0)


def app_store_icon(app_id):
    _, data, _ = get(f'https://itunes.apple.com/lookup?id={app_id}', 2_000_000)
    results = json.loads(data).get('results', [])
    return results[0].get('artworkUrl512') if results else None


def site_icon_candidates(domain):
    """apple-touch-icon and manifest icons declared on the homepage, plus common fallbacks."""
    base = f'https://{domain}/'
    found = []
    try:
        _, html, final = get(base, 2_000_000)
        html = html.decode('utf-8', 'ignore')
        for tag in re.findall(r'<link\b[^>]*>', html, flags=re.I):
            rel = re.search(r'rel=["\']([^"\']+)', tag, re.I)
            href = re.search(r'href=["\']([^"\']+)', tag, re.I)
            if not rel or not href:
                continue
            rel = rel.group(1).lower()
            if 'apple-touch-icon' in rel or rel in ('icon', 'shortcut icon'):
                found.append(urljoin(final, href.group(1)))
            if rel == 'manifest':
                try:
                    _, mdata, mfinal = get(urljoin(final, href.group(1)), 500_000)
                    for icon in json.loads(mdata).get('icons', []):
                        found.append(urljoin(mfinal, icon['src']))
                except Exception:
                    pass
    except Exception:
        pass
    found += [base + 'apple-touch-icon.png',
              f'https://www.google.com/s2/favicons?domain={domain}&sz=256']
    return list(dict.fromkeys(found))


def best_image(urls, kind):
    best = None
    for url in urls:
        try:
            ctype, data, _ = get(url, MAX_BYTES[kind])
            ext = sniff(ctype, data)
            if not ext:
                continue
            size = pixel_size(data, ext)
            if best is None or size[0] > best[3][0]:
                best = (url, data, ext, size)
        except Exception as e:
            print(f'    skip {url}: {e}')
    return best


def main():
    refresh = '--refresh' in sys.argv
    tools = builder.load_tools()
    by_slug = {t['slug']: t for t in tools}
    hero_keys = {}
    for t in tools:  # rendering records every image a page asks for
        if t.get('app_store_id') and not t.get('logo'):
            try:
                t['logo'] = app_store_icon(t['app_store_id'])
                print(f'{t["slug"]}: App Store icon {t["logo"]}')
                src = builder.DATA / f'{t["slug"]}.json'  # remember it so the page build uses it too
                saved = json.loads(src.read_text()); saved['logo'] = t['logo']
                src.write_text(json.dumps(saved, ensure_ascii=False, indent=2) + '\n')
            except Exception as e:
                print(f'{t["slug"]}: App Store lookup failed: {e}')
        for code in builder.LOCALES:
            builder.render(t, code, by_slug)
        own = t.get('logo') or ''
        if own.startswith('http'):
            hero_keys[own] = t['slug']
        elif not own:
            hero_keys['favicon:' + (t.get('logo_domain') or t['domain'])] = t['slug']

    manifest = dict(builder.ASSETS)
    ok = failed = 0
    for key, req in sorted(builder.REQUESTED.items()):
        if key in manifest and not refresh and (ROOT / manifest[key]['path'].lstrip('/')).exists():
            continue
        kind = req['kind']
        print(f'{kind:7} {key}')
        if kind == 'favicon':
            pick = best_image(site_icon_candidates(key.split(':', 1)[1]), kind)
        else:
            pick = best_image([req['url']], kind)
        if not pick:
            failed += 1
            print('    FAILED — page keeps using the remote URL')
            continue
        url, data, ext, size = pick
        folder = 'media' if kind == 'media' else 'logos'
        stem = hero_keys.get(key) or req['name']
        name = f'{stem}-{hashlib.sha1(key.encode()).hexdigest()[:6]}.{ext}' if key not in hero_keys else f'{stem}.{ext}'
        dest = ROOT / 'assets' / folder / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        manifest[key] = {'path': f'/assets/{folder}/{name}', 'source': url, 'width': size[0], 'height': size[1],
                         'fetched': date.today().isoformat()}
        ok += 1
        note = '  ⚠ low resolution for a hero logo' if key in hero_keys and size[0] < MIN_HERO_LOGO else ''
        print(f'    saved {dest.relative_to(ROOT)} ({size[0]}×{size[1]}){note}')

    builder.ASSET_MANIFEST_PATH.write_text(json.dumps(dict(sorted(manifest.items())), ensure_ascii=False, indent=2) + '\n')
    print(f'\nDone: {ok} downloaded, {failed} failed, {len(manifest)} assets in data/assets.json')


if __name__ == '__main__':
    main()
