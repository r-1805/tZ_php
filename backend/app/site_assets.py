from __future__ import annotations

import json
import struct
import zlib
from html import escape
from typing import Any


def build_font_css(font_theme: dict[str, Any] | None = None) -> str:
    font_theme = font_theme or {}
    faces = font_theme.get("faces", [])
    body_stack = font_theme.get("body_stack", '"Avenir Next", "Trebuchet MS", "Segoe UI", sans-serif')
    heading_stack = font_theme.get("heading_stack", 'Georgia, "Times New Roman", serif')
    accent_stack = font_theme.get("accent_stack", body_stack)
    face_rules = []
    for face in faces:
        face_rules.append(
            """
@font-face {{
  font-family: "{family}";
  src: url("{src}") format("{format}");
  font-weight: {weight};
  font-style: {style};
  font-display: swap;
}}
""".format(
                family=face["family"],
                src=face["src"],
                format=face["format"],
                weight=face["weight"],
                style=face.get("style", "normal"),
            )
        )
    return """
:root {{
  --font-body: {body_stack};
  --font-heading: {heading_stack};
  --font-accent: {accent_stack};
}}
{faces}
""".format(
        body_stack=body_stack,
        heading_stack=heading_stack,
        accent_stack=accent_stack,
        faces="".join(face_rules),
    )


def build_base_css() -> str:
    return """
* {
  box-sizing: border-box;
}
html {
  scroll-behavior: smooth;
}
body {
  margin: 0;
}
img {
  max-width: 100%;
  display: block;
}
ul {
  margin: 0;
  padding-left: 20px;
}
"""


def build_layout_css() -> str:
    return """
body {
  font-family: var(--font-body);
}
.shell {
  width: min(1120px, calc(100% - 32px));
  margin: 0 auto;
}
.site-header {
  position: sticky;
  top: 0;
  z-index: 10;
}
.site-header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 18px 0;
}
.site-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 14px;
}
.hero {
  padding: 84px 0 56px;
}
.hero__grid {
  display: grid;
  grid-template-columns: 1.3fr 0.9fr;
  gap: 30px;
  align-items: stretch;
}
.hero__main,
.panel {
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.hero__main {
  position: relative;
  overflow: hidden;
  padding: 40px;
}
.hero__visual {
  display: grid;
  gap: 18px;
}
.hero__visual-card {
  overflow: hidden;
}
.hero__visual-card img {
  width: 100%;
  border-radius: 18px;
}
.hero__support {
  display: grid;
  gap: 16px;
}
.hero__support .panel {
  min-height: 0;
}
.section {
  padding: 28px 0 20px;
}
.section--spacious {
  padding: 52px 0 28px;
}
.section__header {
  margin-bottom: 20px;
}
.section__eyebrow {
  display: inline-block;
  margin-bottom: 12px;
}
.copy {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}
.stack {
  display: grid;
  gap: 18px;
}
.grid-three {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}
.grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}
.metrics-band {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 28px;
}
.split-feature {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 24px;
  align-items: center;
}
.gallery-strip {
  display: grid;
  grid-template-columns: 1.25fr 0.75fr 0.75fr;
  gap: 18px;
}
.timeline {
  display: grid;
  gap: 14px;
}
.contact-shell {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 24px;
}
.site-footer {
  margin-top: 40px;
  padding: 36px 0 56px;
}
.site-footer__grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr;
  gap: 24px;
}
@media (max-width: 920px) {
  .hero__grid,
  .copy,
  .site-footer__grid,
  .grid-three,
  .grid-two,
  .metrics-band,
  .split-feature,
  .gallery-strip,
  .contact-shell {
    grid-template-columns: 1fr;
  }
  .site-header__inner {
    align-items: flex-start;
    flex-direction: column;
  }
  .hero__main {
    padding: 28px;
  }
}
"""


def build_components_css() -> str:
    return """
a {
  color: var(--accent-dark);
  text-decoration: none;
}
a:hover {
  color: var(--accent);
}
.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  font-weight: 800;
  letter-spacing: 0.02em;
}
.site-nav a {
  position: relative;
  padding-bottom: 4px;
}
.site-nav a::after {
  content: "";
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 2px;
  background: currentColor;
  transform: scaleX(0);
  transform-origin: left;
  transition: transform .25s ease;
}
.site-nav a:hover::after,
.site-nav a[aria-current="page"]::after {
  transform: scaleX(1);
}
.brand__mark {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  color: white;
  font-size: 14px;
}
.kicker {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 800;
}
h1,
h2,
h3 {
  font-family: var(--font-heading);
  line-height: 1.08;
  margin: 0 0 16px;
}
h1 {
  font-size: clamp(40px, 7vw, 68px);
  max-width: 12ch;
}
h2 {
  font-size: clamp(28px, 4vw, 40px);
}
h3 {
  font-size: 22px;
}
.lead {
  font-size: 18px;
  line-height: 1.7;
  max-width: 60ch;
}
.actions,
.tag-row,
.cookie-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.actions {
  margin-top: 24px;
}
.btn {
  position: relative;
  overflow: hidden;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 14px 18px;
  min-height: 48px;
  border-radius: 999px;
  font-weight: 800;
  border: 1px solid transparent;
  transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
}
.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.16);
}
.panel {
  padding: 28px;
}
.panel dl {
  margin: 0;
  display: grid;
  gap: 14px;
}
.panel dt {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 4px;
  font-weight: 800;
}
.panel dd {
  margin: 0;
  font-size: 16px;
}
.card {
  border-radius: 18px;
  padding: 22px;
  transition: transform .28s ease, box-shadow .28s ease, border-color .28s ease;
}
.card-hover,
.card:hover {
  transform: translateY(-6px);
}
.metric-card {
  padding: 20px;
  border-radius: 20px;
}
.metric-card strong {
  display: block;
  font-size: clamp(28px, 4vw, 42px);
  margin-bottom: 8px;
}
.media-card {
  position: relative;
  overflow: hidden;
  min-height: 220px;
  border-radius: 24px;
}
.media-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.media-card--tall {
  min-height: 100%;
}
.media-card__caption {
  position: absolute;
  left: 18px;
  right: 18px;
  bottom: 18px;
  padding: 14px 16px;
  border-radius: 16px;
  color: white;
  background: linear-gradient(180deg, rgba(15,23,42,0.05), rgba(15,23,42,0.74));
}
.list-checks {
  display: grid;
  gap: 12px;
  list-style: none;
  padding: 0;
}
.list-checks li {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.list-checks li::before {
  content: "•";
  color: var(--accent);
  font-size: 22px;
  line-height: 1;
}
.timeline__item {
  display: grid;
  grid-template-columns: 52px 1fr;
  gap: 14px;
  align-items: start;
}
.timeline__step {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 18px;
  font-weight: 800;
}
.showcase-quote {
  padding: 28px;
  border-radius: 24px;
}
.faq-item {
  padding: 18px 0;
  border-top: 1px solid var(--border);
}
.faq-item:first-child {
  border-top: 0;
}
.tag-row {
  margin-top: 18px;
}
.tag-row--footer {
  margin-top: 0;
}
.tag {
  padding: 10px 12px;
  border-radius: 999px;
  font-size: 13px;
}
.cta-banner {
  margin: 32px 0 12px;
  border-radius: 26px;
  padding: 28px;
}
.muted {
  color: var(--muted);
}
#cookie-banner {
  position: fixed;
  right: 16px;
  bottom: 16px;
  width: min(420px, calc(100% - 32px));
  z-index: 20;
}
.cookie-card {
  border-radius: 20px;
  padding: 18px;
}
.cookie-actions button {
  cursor: pointer;
  border: 0;
  border-radius: 999px;
  padding: 12px 14px;
  font-weight: 800;
}
.reveal {
  opacity: 0;
  transform: translateY(24px);
  transition: opacity .7s ease, transform .7s ease;
}
.reveal.is-visible {
  opacity: 1;
  transform: translateY(0);
}
"""


def build_legal_css() -> str:
    return """
.legal-page,
.error-page {
  padding: 56px 0 24px;
}
.legal-page h2 {
  margin-top: 28px;
}
.legal-page p,
.card p,
.copy p,
.faq-item p {
  margin: 0 0 14px;
  line-height: 1.75;
  color: var(--muted);
}
.legal-page ul {
  padding-left: 20px;
  color: var(--muted);
  line-height: 1.7;
}
.contact-list {
  display: grid;
  gap: 10px;
  list-style: none;
  padding: 0;
}
.contact-list li {
  line-height: 1.7;
  color: var(--muted);
}
.contact-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 18px;
}
.contact-grid dt {
  font-size: 12px;
  letter-spacing: .08em;
  text-transform: uppercase;
}
.contact-grid dd {
  margin: 4px 0 0;
}
@media (max-width: 920px) {
  .contact-grid {
    grid-template-columns: 1fr;
  }
}
"""


def build_css(palette: dict[str, str]) -> str:
    return f"""
:root {{
  --bg: {palette['bg']};
  --surface: {palette['surface']};
  --accent: {palette['accent']};
  --accent-dark: {palette['accent_dark']};
  --ink: {palette['ink']};
  --muted: {palette['muted']};
  --border: rgba(15, 23, 42, 0.12);
  --radius: 22px;
  --shadow: 0 20px 60px rgba(15, 23, 42, 0.08);
}}
body {{
  margin: 0;
  color: var(--ink);
  background:
    radial-gradient(circle at top right, rgba(255,255,255,0.96), transparent 32%),
    radial-gradient(circle at left 20%, {palette['accent']}12, transparent 28%),
    linear-gradient(180deg, var(--bg) 0%, #ffffff 58%, var(--surface) 100%);
}}
.site-header {{
  background: rgba(255,255,255,0.86);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border);
}}
  color: var(--ink);
.brand__mark {{
  background: linear-gradient(135deg, var(--accent), var(--accent-dark));
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.16);
}}
.hero__main, .panel {{
  background: rgba(255,255,255,0.8);
  border: 1px solid var(--border);
}}
.hero__main::before {{
  content: "";
  position: absolute;
  inset: auto -40px -60px auto;
  width: 180px;
  height: 180px;
  border-radius: 999px;
  background: linear-gradient(135deg, {palette['accent']}22, transparent);
}}
.kicker {{
  background: rgba(255,255,255,0.8);
  border: 1px solid rgba(15,23,42,0.1);
  color: var(--accent-dark);
}}
.lead {{
  color: var(--muted);
}}
.btn--primary {{
  background: linear-gradient(135deg, var(--accent), var(--accent-dark));
  color: white;
}}
.btn--secondary {{
  background: rgba(255,255,255,0.85);
  border-color: rgba(15,23,42,0.12);
}}
.panel dt {{
  color: var(--muted);
}}
.card {{
  background: rgba(255,255,255,0.86);
  border: 1px solid var(--border);
}}
.metric-card,
.timeline__step,
.showcase-quote {{
  background: rgba(255,255,255,0.86);
  border: 1px solid var(--border);
}}
.tag {{
  background: rgba(255,255,255,0.8);
  border: 1px solid var(--border);
  color: var(--muted);
}}
.cta-banner {{
  background: linear-gradient(135deg, var(--accent-dark), var(--accent));
  color: white;
  box-shadow: 0 22px 60px rgba(15,23,42,0.15);
}}
.cta-banner p {{
  color: rgba(255,255,255,0.86);
}}
.site-footer {{
  border-top: 1px solid var(--border);
}}
.muted {{
  color: var(--muted);
}}
#cookie-banner {{
}}
.cookie-card {{
  background: rgba(255,255,255,0.94);
  border: 1px solid var(--border);
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.18);
}}
.cookie-actions {{
  margin-top: 14px;
}}
.cookie-actions button {{
  background: linear-gradient(135deg, var(--accent), var(--accent-dark));
  color: white;
}}
"""


def build_cookie_script() -> str:
    return """
(() => {
  const key = 'siteConsentAccepted';
  const root = document.getElementById('cookie-banner');
  if (!root) return;
  if (localStorage.getItem(key) === 'yes') {
    root.remove();
    return;
  }
  const button = root.querySelector('[data-cookie-accept]');
  button?.addEventListener('click', () => {
    localStorage.setItem(key, 'yes');
    root.remove();
  });
})();
"""


def build_navigation_script() -> str:
    return """
(() => {
  const currentPath = window.location.pathname.split('/').pop() || 'index.php';
  const links = document.querySelectorAll('.site-nav a');
  for (const link of links) {
    const href = link.getAttribute('href');
    if (href && href.endsWith(currentPath)) {
      link.setAttribute('aria-current', 'page');
    }
  }
})();
"""


def build_site_script() -> str:
    return """
(() => {
  const links = document.querySelectorAll('a[href^="#"]');
  for (const link of links) {
    link.addEventListener('click', (event) => {
      const href = link.getAttribute('href');
      if (!href || href.length < 2) return;
      const target = document.querySelector(href);
      if (!target) return;
      event.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }
})();
"""


def build_interactions_script() -> str:
    return """
(() => {
  const revealItems = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealItems.length) {
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      }
    }, { threshold: 0.16 });
    for (const item of revealItems) observer.observe(item);
  } else {
    for (const item of revealItems) item.classList.add('is-visible');
  }
  const cards = document.querySelectorAll('.card');
  for (const card of cards) {
    card.addEventListener('mouseenter', () => card.classList.add('card-hover'));
    card.addEventListener('mouseleave', () => card.classList.remove('card-hover'));
  }
})();
"""


def build_webmanifest(brand_display: str, accent_color: str) -> str:
    manifest = {
        "name": brand_display,
        "short_name": brand_display[:24],
        "icons": [
            {"src": "/apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
            {"src": "/favicon-32x32.png", "sizes": "32x32", "type": "image/png"},
            {"src": "/favicon-16x16.png", "sizes": "16x16", "type": "image/png"},
        ],
        "theme_color": accent_color,
        "background_color": "#ffffff",
        "display": "standalone",
    }
    return json.dumps(manifest, indent=2)


def build_robots_txt(domain: str) -> str:
    return "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "",
            f"Sitemap: https://{domain}/sitemap.xml",
        ]
    )


def build_sitemap_xml(domain: str, page_files: list[str]) -> str:
    urls = []
    for page_file in page_files:
        if not page_file.endswith(".php") or page_file == "404.php":
            continue
        urls.append(
            f"""  <url>
    <loc>https://{domain}/{page_file}</loc>
    <changefreq>weekly</changefreq>
    <priority>{"1.0" if page_file == "index.php" else "0.7"}</priority>
  </url>"""
        )
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            *urls,
            "</urlset>",
        ]
    )


def build_htaccess() -> str:
    return "\n".join(
        [
            "Options -Indexes",
            "DirectoryIndex index.php",
            "ErrorDocument 404 /404.php",   # === ANTI‑AI FINGERPRINT PATCH ===
            "",
            "<IfModule mod_rewrite.c>",
            "RewriteEngine On",
            "RewriteCond %{REQUEST_FILENAME} !-f",
            "RewriteCond %{REQUEST_FILENAME} !-d",
            "RewriteRule ^(.+)$ $1.php [L]",
            "</IfModule>",
            "",
            "<IfModule mod_headers.c>",
            'Header set X-Content-Type-Options "nosniff"',
            'Header set Referrer-Policy "strict-origin-when-cross-origin"',
            'Header set X-Frame-Options "SAMEORIGIN"',
            "</IfModule>",
        ]
    )


def build_favicon_ico(hex_color: str) -> bytes:
    return build_png_square(32, hex_color)


def build_favicon_svg(brand_display: str, palette: dict[str, str]) -> str:
    initials = "".join(part[0] for part in brand_display.split()[:2]).upper() or "S"
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{escape(brand_display)}">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{palette['accent']}"/>
      <stop offset="100%" stop-color="{palette['accent_dark']}"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="18" fill="url(#g)"/>
  <text x="32" y="39" text-anchor="middle" font-size="24" font-family="Segoe UI, sans-serif" font-weight="800" fill="#fff">{escape(initials)}</text>
</svg>
""".strip()


def build_pattern_svg(brand_display: str, palette: dict[str, str]) -> str:
    initials = "".join(part[0] for part in brand_display.split()[:2]).upper() or "S"
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 620" role="img" aria-label="{escape(brand_display)} pattern">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{palette['accent']}"/>
      <stop offset="100%" stop-color="{palette['accent_dark']}"/>
    </linearGradient>
  </defs>
  <rect width="860" height="620" rx="36" fill="url(#bg)"/>
  <circle cx="142" cy="126" r="82" fill="rgba(255,255,255,0.10)"/>
  <circle cx="714" cy="136" r="58" fill="rgba(255,255,255,0.14)"/>
  <circle cx="740" cy="470" r="102" fill="rgba(255,255,255,0.08)"/>
  <path d="M84 450C210 362 324 340 428 386C526 430 618 426 766 326" fill="none" stroke="rgba(255,255,255,0.22)" stroke-width="26" stroke-linecap="round"/>
  <rect x="102" y="160" width="262" height="182" rx="24" fill="rgba(255,255,255,0.10)"/>
  <rect x="394" y="220" width="302" height="224" rx="28" fill="rgba(255,255,255,0.12)"/>
  <text x="128" y="274" font-size="112" font-family="Segoe UI, Trebuchet MS, sans-serif" font-weight="800" fill="#ffffff">{escape(initials)}</text>
  <text x="126" y="326" font-size="24" font-family="Segoe UI, Trebuchet MS, sans-serif" fill="rgba(255,255,255,0.82)">{escape(brand_display)}</text>
</svg>
""".strip()


def build_contact_pattern_svg(brand_display: str, palette: dict[str, str]) -> str:
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 420" role="img" aria-label="{escape(brand_display)} contact pattern">
  <rect width="860" height="420" rx="28" fill="{palette['surface']}"/>
  <circle cx="148" cy="140" r="72" fill="{palette['accent']}22"/>
  <circle cx="706" cy="98" r="56" fill="{palette['accent_dark']}22"/>
  <circle cx="640" cy="322" r="94" fill="{palette['accent']}16"/>
  <path d="M110 320C236 244 354 222 478 264C578 298 668 294 780 224" fill="none" stroke="{palette['accent_dark']}" stroke-opacity="0.24" stroke-width="18" stroke-linecap="round"/>
  <rect x="126" y="126" width="194" height="112" rx="20" fill="{palette['accent_dark']}" fill-opacity="0.12"/>
  <rect x="372" y="172" width="288" height="154" rx="22" fill="{palette['accent']}" fill-opacity="0.12"/>
</svg>
""".strip()


def build_footer_pattern_svg(brand_display: str, palette: dict[str, str]) -> str:
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 220" role="img" aria-label="{escape(brand_display)} footer pattern">
  <rect width="860" height="220" rx="22" fill="{palette['bg']}"/>
  <path d="M40 156C162 82 262 66 368 108C474 150 584 150 820 68" fill="none" stroke="{palette['accent']}" stroke-opacity="0.22" stroke-width="16" stroke-linecap="round"/>
  <circle cx="124" cy="68" r="32" fill="{palette['accent_dark']}22"/>
  <circle cx="742" cy="148" r="48" fill="{palette['accent']}1f"/>
</svg>
""".strip()


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def build_png_square(size: int, hex_color: str) -> bytes:
    color = hex_color.lstrip("#")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    alpha = 255
    row = bytes([red, green, blue, alpha]) * size
    raw = b"".join(b"\x00" + row for _ in range(size))
    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", header),
            _png_chunk(b"IDAT", zlib.compress(raw, 9)),
            _png_chunk(b"IEND", b""),
        ]
    )
