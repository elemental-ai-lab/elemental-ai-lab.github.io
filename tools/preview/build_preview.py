#!/usr/bin/env python3
"""Build a single-file preview of the built site (all pages, hash routing, assets inlined).

    jekyll build && python3 tools/preview/build_preview.py --site _site --out preview.html

--variants adds a Primary/Sparse switch to the Home banner (for review only; the
production site always uses the primary artwork).
"""
import argparse, base64, json, mimetypes, re
from pathlib import Path

MIME = {".svg": "image/svg+xml", ".woff2": "font/woff2", ".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg"}
PAGES = {"/": "index.html", "/team/": "team/index.html", "/join/": "join/index.html",
         "/team/christian-naesseth/": "team/christian-naesseth/index.html", "/404.html": "404.html"}


def data_uri(path: Path) -> str:
    mime = MIME.get(path.suffix, mimetypes.guess_type(str(path))[0] or "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="_site")
    ap.add_argument("--out", default="preview.html")
    ap.add_argument("--variants", action="store_true")
    a = ap.parse_args()
    site = Path(a.site)
    index = (site / "index.html").read_text()

    css = []
    for href in re.findall(r'<link rel="stylesheet" href="([^"]+)"', index):
        p = site / href.lstrip("/")
        text = p.read_text()
        text = re.sub(r'url\((["\']?)(?!data:)([^)"\']+)\1\)',
                      lambda m: f'url("{data_uri((p.parent / m.group(2)).resolve())}")', text)
        css.append(text)
    if a.variants:
        banner = site / "images/banner"
        css.append(f"""
.masthead--home[data-banner="sparse"] .masthead-art {{ background-image: url("{data_uri(banner / 'masthead-wide-sparse.svg')}"); }}
@media (max-width: 1023px) {{ .masthead--home[data-banner="sparse"] .masthead-art {{ background-image: url("{data_uri(banner / 'masthead-medium-sparse.svg')}"); }} }}
@media (max-width: 639px) {{ .masthead--home[data-banner="sparse"] .masthead-art {{ background-image: url("{data_uri(banner / 'masthead-narrow-sparse.svg')}"); }} }}
.banner-options {{ position: fixed; left: 12px; bottom: 12px; z-index: 9; display: flex; gap: 2px; padding: 3px;
  background: var(--masthead-paper); border: 1px solid var(--line); border-radius: 6px; font: 500 12px/1 var(--body); }}
.banner-options button {{ border: 0; background: none; padding: 6px 9px; border-radius: 4px; color: var(--masthead-ink); cursor: pointer; font: inherit; }}
.banner-options button[aria-pressed="true"] {{ background: var(--wash); color: var(--masthead-current); }}""")

    images, pages = {}, {}
    def img_key(src):
        p = site / src.lstrip("/")
        images.setdefault(src, data_uri(p))
        return src
    for route, file in PAGES.items():
        html = (site / file).read_text()
        title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
        body = re.search(r"<body[^>]*>(.*)</body>", html, re.S).group(1)
        body = re.sub(r'src="(/[^"]+)"', lambda m: f'data-preview-src="{img_key(m.group(1))}"', body)
        # internal links -> hash routes; in-page anchors keep their page
        body = re.sub(r'href="/([^"]*)"', lambda m: f'href="#/{m.group(1)}"', body)
        body = re.sub(r'href="#(?!/)([^"]+)"', lambda m: f'href="#{route}#{m.group(1)}"', body)
        pages[route] = {"title": title, "body": body}

    motion = (site / "assets/motion.js").read_text()
    data = json.dumps({"pages": pages, "images": images}).replace("</", "<\\/")
    switch = ('<div class="banner-options" role="group" aria-label="Banner variant (preview only)">'
              '<button type="button" data-v="primary" aria-pressed="true">Primary</button>'
              '<button type="button" data-v="sparse" aria-pressed="false">Sparse</button></div>') if a.variants else ""
    out = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Elemental AI Lab (preview)</title>
<style>{''.join(css)}</style></head><body>
<div id="app"></div>{switch}
<script type="application/json" id="preview-data">{data}</script>
<script>
const D = JSON.parse(document.getElementById('preview-data').textContent);
let variant = 'primary', lastRoute = null;
function motion() {{ {motion} }}
function render() {{
  const h = location.hash.slice(1) || '/';
  const i = h.indexOf('#', 1);
  let route = i > 0 ? h.slice(0, i) : h, frag = i > 0 ? h.slice(i + 1) : '';
  if (!D.pages[route]) route = '/404.html';
  const p = D.pages[route];
  document.title = p.title.replace(/&amp;/g, '&');
  const app = document.getElementById('app');
  app.innerHTML = p.body;
  app.querySelectorAll('[data-preview-src]').forEach(el => el.src = D.images[el.dataset.previewSrc]);
  const mh = app.querySelector('.masthead--home'); if (mh) mh.dataset.banner = variant;
  const sw = document.querySelector('.banner-options'); if (sw) sw.hidden = !mh;
  motion();
  const t = frag && document.getElementById(frag);
  if (t) {{
    t.scrollIntoView();
    if (!t.hasAttribute('tabindex')) t.setAttribute('tabindex', '-1');
    t.focus({{ preventScroll: true }});
  }} else {{
    window.scrollTo(0, 0);
    const m = document.getElementById('main');
    if (m && lastRoute !== null && lastRoute !== route) m.focus({{ preventScroll: true }});
  }}
  lastRoute = route;
}}
document.querySelectorAll('.banner-options button').forEach(b => b.addEventListener('click', () => {{
  variant = b.dataset.v;
  document.querySelectorAll('.banner-options button').forEach(x => x.setAttribute('aria-pressed', x === b));
  const mh = document.querySelector('.masthead--home'); if (mh) mh.dataset.banner = variant;
}}));
addEventListener('hashchange', render); render();
</script></body></html>"""
    Path(a.out).write_text(out)
    print(f"wrote {a.out} ({len(out) / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
