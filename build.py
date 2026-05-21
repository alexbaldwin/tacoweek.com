#!/usr/bin/env python3
"""Build the static Taco Week site from the archived Medium RSS content.

Reads raw/posts.json (extracted from medium.com/feed/taco-week) and emits a
plain static site into public/ -- one landing page plus one page per post,
complete with SEO metadata, Open Graph / Twitter cards, JSON-LD structured
data, a sitemap and robots.txt. Output is dependency-free HTML/CSS.
"""
import json
import re
import html
from pathlib import Path
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse, parse_qs, unquote

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"
POSTS = json.load(open(ROOT / "raw" / "posts.json"))

# --- Site config -------------------------------------------------------------
BASE_URL = "https://tacoweek.com"          # production origin (no trailing slash)
SITE_NAME = "Taco Week"
AUTHOR = "Alex Baldwin"
ILLUSTRATOR = "Laura Bohill"
ILLUSTRATOR_URL = "https://twitter.com/LauRARbee"
TAGLINE = "It’s like shark week, but for tacos"
THEME_COLOR = "#d6452b"

# Drop Medium's trailing hex hash from each slug (e.g. street-tacos-682496bfc937).
for _p in POSTS:
    _p["slug"] = re.sub(r"-[0-9a-f]{6,}$", "", _p["slug"])

# Map each post's remote illustration filename -> the local copy we downloaded.
ILLUSTRATION = {
    "street-tacos": "0*kIGYyzI7htP1gHvN.png",
    "fancy-tacos": "0*CGFt8sOnbmr-mAIn.png",
    "dessert-tacos": "0*ehr4EE6T3i70Ghmr.png",
    "breakfast-tacos": "0*UW6lIe1lR6nHQUdX.png",
    "fusion-tacos": "0*P0eMyUFD8yAoPor4.png",
    "future-tacos": "0*N9FXDPMtR4aRWvef.png",
}
SLUGS = {p["slug"] for p in POSTS}


def fmt_date(pubdate: str):
    dt = parsedate_to_datetime(pubdate)
    return dt.strftime("%Y-%m-%d"), dt.strftime("%B %-d, %Y"), dt.isoformat()


def plain_text(content_html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", content_html)).strip()


def embed_from_embedly(iframe_src: str):
    """Turn a Medium/embedly iframe into a clean responsive YouTube/Vimeo embed."""
    qs = parse_qs(urlparse(html.unescape(iframe_src)).query)
    inner = unquote(qs.get("src", [""])[0])
    yt = re.search(r"youtube\.com/embed/([\w-]+)", inner)
    if yt:
        return (f'<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/{yt.group(1)}" '
                f'title="YouTube video" loading="lazy" allowfullscreen '
                f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"></iframe></div>')
    vm = re.search(r"player\.vimeo\.com/video/(\d+)", inner)
    if vm:
        return (f'<div class="video"><iframe src="https://player.vimeo.com/video/{vm.group(1)}" '
                f'title="Vimeo video" loading="lazy" allowfullscreen></iframe></div>')
    return None


def clean_content(post: dict) -> str:
    c = post["content"]
    slug = post["slug"]

    # Point the lead illustration at the local copy (and give it real alt + dimensions later).
    remote = re.escape("https://cdn-images-1.medium.com/max/400/" + ILLUSTRATION[slug])
    c = re.sub(remote, f"images/{slug}.png", c)

    # Replace embedly iframes with clean responsive embeds.
    c = re.sub(r'<iframe src="(https://cdn\.embedly\.com[^"]+)"[^>]*>.*?</iframe>',
               lambda m: embed_from_embedly(m.group(1)) or "", c, flags=re.S)

    # Strip Medium's tracking pixel and trailing "originally published in" footer.
    c = re.sub(r'<img src="https://medium\.com/_/stat[^>]*>', "", c)
    c = re.sub(r'<hr\s*/?>\s*<p><a href="https://medium\.com/taco-week/[^<]*</a> was originally published.*?</p>',
               "", c, flags=re.S)
    # Drop the circular "Originally published at tacoweek.com" line (this *is* that site now).
    c = re.sub(r'<p><em>Originally published at\s*</em><a [^>]*>.*?</a><em>\.</em></p>', "", c, flags=re.S)

    # Rewrite self-referential links to the old tacoweek.com/.org as relative page links.
    def selflink(m):
        target = m.group(1)
        frag = m.group(3) or ""
        return f'href="{target}.html{frag}"' if target in SLUGS else m.group(0)
    c = re.sub(r'href="https?://tacoweek\.(?:com|org)/([a-z-]+)(\.html)?(#[\w-]+)?"', selflink, c)

    # Demote content headings so the document outline is h1 > h2 > h3 (a11y / SEO).
    # The recipe section heading (originally h3) becomes the page's first h2 and gets an id.
    first = {"done": False}
    def demote_h3(m):
        if not first["done"]:
            first["done"] = True
            return f'<h2 id="recipes">{m.group(1)}</h2>'
        return f'<h2>{m.group(1)}</h2>'
    c = re.sub(r'<h3>(.*?)</h3>', demote_h3, c, flags=re.S)
    c = re.sub(r'<h4>(.*?)</h4>', r'<h3>\1</h3>', c, flags=re.S)

    # Give the lead illustration descriptive alt text; drop the void-element trailing slash.
    alt = html.escape(f'{post["title"]} illustration by {ILLUSTRATOR}')
    c = re.sub(r'<img alt="" src="images/' + re.escape(slug) + r'\.png"\s*/?>',
               f'<img src="images/{slug}.png" alt="{alt}" width="400" loading="lazy">', c)

    return c.strip()


def head(*, title, description, canonical, og_type, og_image, image_alt, extra=""):
    img_abs = f"{BASE_URL}/{og_image}"
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta name="theme-color" content="{THEME_COLOR}">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="images/logo.gif">
<link rel="apple-touch-icon" href="images/logo.gif">
<meta property="og:site_name" content="{html.escape(SITE_NAME)}">
<meta property="og:locale" content="en_US">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{img_abs}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{html.escape(image_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(title)}">
<meta name="twitter:description" content="{html.escape(description)}">
<meta name="twitter:image" content="{img_abs}">
<meta name="twitter:image:alt" content="{html.escape(image_alt)}">
{extra}<link rel="stylesheet" href="style.css">"""


def page(*, title, description, canonical, og_type, og_image, image_alt, body, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head(title=title, description=description, canonical=canonical, og_type=og_type, og_image=og_image, image_alt=image_alt, extra=extra_head)}
</head>
<body>
<header class="site-header">
  <a class="brand" href="index.html">
    <img src="images/logo.gif" alt="" width="48" height="48">
    <span>Taco Week</span>
  </a>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <p>{html.escape(TAGLINE)}</p>
  <p>Illustrations by <a href="{ILLUSTRATOR_URL}" rel="noopener">{ILLUSTRATOR}</a>. Words by {AUTHOR}, 2015.</p>
</footer>
</body>
</html>
"""


def jsonld(data: dict) -> str:
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>\n'


def build_post(post, prev_post, next_post):
    iso, pretty, isofull = fmt_date(post["pubDate"])
    slug = post["slug"]
    canonical = f"{BASE_URL}/{slug}.html"
    description = plain_text(post["content"])[:155].rstrip() + "…"
    og_image = f"images/og/{slug}.png"

    ld = jsonld({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": post["title"],
        "description": description,
        "image": [f"{BASE_URL}/{og_image}", f"{BASE_URL}/images/{slug}.png"],
        "datePublished": isofull,
        "dateModified": isofull,
        "author": {"@type": "Person", "name": AUTHOR},
        "publisher": {"@type": "Organization", "name": SITE_NAME,
                      "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/images/logo.gif"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "keywords": ", ".join(post.get("cats", [])),
    })

    body = f"""<article class="post">
  <a class="back" href="index.html">← All tacos</a>
  <h1>{html.escape(post['title'])}</h1>
  <p class="byline"><time datetime="{iso}">{pretty}</time> · {html.escape(AUTHOR)}</p>
  <div class="prose">
{clean_content(post)}
  </div>
  <nav class="post-nav">
    {f'<a class="prev" href="{prev_post["slug"]}.html">← {html.escape(prev_post["title"])}</a>' if prev_post else '<span></span>'}
    {f'<a class="next" href="{next_post["slug"]}.html">{html.escape(next_post["title"])} →</a>' if next_post else '<span></span>'}
  </nav>
</article>"""
    out = page(title=f"{post['title']} — {SITE_NAME}", description=description, canonical=canonical,
               og_type="article", og_image=og_image, image_alt=f"{post['title']} — {SITE_NAME}",
               body=body, extra_head=ld)
    (PUBLIC / f"{slug}.html").write_text(out, encoding="utf-8")


def build_index():
    cards = []
    list_items = []
    for i, post in enumerate(POSTS, 1):
        excerpt = plain_text(post["content"])[:140]
        cards.append(f"""    <a class="card" href="{post['slug']}.html">
      <span class="day">Day {i}</span>
      <img src="images/{post['slug']}.png" alt="{html.escape(post['title'])} illustration by {ILLUSTRATOR}" width="400" loading="lazy">
      <h2>{html.escape(post['title'])}</h2>
      <p>{html.escape(excerpt)}…</p>
    </a>""")
        list_items.append({"@type": "ListItem", "position": i,
                           "url": f"{BASE_URL}/{post['slug']}.html", "name": post["title"]})

    ld = jsonld({
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": SITE_NAME,
        "description": TAGLINE,
        "url": f"{BASE_URL}/",
        "author": {"@type": "Person", "name": AUTHOR},
        "publisher": {"@type": "Organization", "name": SITE_NAME,
                      "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/images/logo.gif"}},
        "blogPost": [{"@type": "BlogPosting", "headline": p["title"],
                      "url": f"{BASE_URL}/{p['slug']}.html",
                      "datePublished": fmt_date(p["pubDate"])[2]} for p in POSTS],
    })
    ld += jsonld({"@context": "https://schema.org", "@type": "ItemList", "itemListElement": list_items})

    body = f"""<section class="hero">
  <img class="hero-logo" src="images/logo.gif" alt="Taco Week logo — a dancing taco" width="120" height="120">
  <h1>Taco Week</h1>
  <p class="tagline">{html.escape(TAGLINE)}</p>
  <p class="intro">Six glorious kinds of taco. A celebration of the world’s greatest food,
  one corn tortilla at a time.</p>
</section>
<section class="grid">
{chr(10).join(cards)}
</section>"""
    out = page(title=f"{SITE_NAME} — {TAGLINE}", description=TAGLINE, canonical=f"{BASE_URL}/",
               og_type="website", og_image="images/og/index.png", image_alt=f"{SITE_NAME} — {TAGLINE}",
               body=body, extra_head=ld)
    (PUBLIC / "index.html").write_text(out, encoding="utf-8")


def build_sitemap_robots():
    urls = [(f"{BASE_URL}/", "1.0")] + [(f"{BASE_URL}/{p['slug']}.html", "0.8") for p in POSTS]
    lastmod = max(fmt_date(p["pubDate"])[2] for p in POSTS)
    entries = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{lastmod}</lastmod><priority>{pr}</priority></url>"
        for u, pr in urls)
    (PUBLIC / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n',
        encoding="utf-8")
    (PUBLIC / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
    # GitHub Pages custom-domain marker (published at the site root).
    (PUBLIC / "CNAME").write_text(urlparse(BASE_URL).netloc + "\n", encoding="utf-8")


def build_og_cards():
    """Write per-page HTML cards (1200x630) for screenshotting into images/og/*.png."""
    og_dir = ROOT / "_ogcards"
    og_dir.mkdir(exist_ok=True)
    cards = {"index": ("Taco Week", TAGLINE, None)}
    for i, p in enumerate(POSTS, 1):
        cards[p["slug"]] = (p["title"], f"Day {i} of Taco Week", p["slug"])
    for name, (title, subtitle, slug) in cards.items():
        img = f'<img src="../public/images/{slug}.png" alt="">' if slug else \
              '<img class="logo" src="../public/images/logo.gif" alt="">'
        (og_dir / f"{name}.html").write_text(f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{margin:0;box-sizing:border-box}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{display:flex;align-items:center;gap:48px;padding:80px;
  background:linear-gradient(135deg,#fff4e0,#ffe7c2);font-family:-apple-system,Helvetica,Arial,sans-serif;color:#20140a}}
.text{{flex:1}}
.eyebrow{{display:inline-block;background:#d6452b;color:#fff;font-weight:700;text-transform:uppercase;
  letter-spacing:.08em;font-size:24px;padding:6px 18px;border-radius:999px;margin-bottom:28px}}
h1{{font-size:96px;line-height:.95;letter-spacing:-.03em;margin:0 0 20px}}
p{{font-size:38px;color:#a8552f;font-style:italic;margin:0}}
.art{{width:420px;height:470px;display:flex;align-items:center;justify-content:center}}
.art img{{max-width:100%;max-height:100%;object-fit:contain;filter:drop-shadow(0 20px 40px rgba(32,20,10,.25))}}
.art img.logo{{border-radius:50%}}
</style></head><body>
<div class="text"><span class="eyebrow">{html.escape(subtitle)}</span><h1>{html.escape(title)}</h1>
<p>{html.escape(TAGLINE if slug else "")}</p></div>
<div class="art">{img}</div>
</body></html>""", encoding="utf-8")
    return list(cards.keys())


def main():
    PUBLIC.mkdir(exist_ok=True)
    (PUBLIC / "images" / "og").mkdir(parents=True, exist_ok=True)
    for i, post in enumerate(POSTS):
        build_post(post, POSTS[i - 1] if i > 0 else None,
                   POSTS[i + 1] if i < len(POSTS) - 1 else None)
    build_index()
    build_sitemap_robots()
    build_og_cards()
    print(f"Built {len(POSTS)} posts + index, sitemap, robots, and OG card templates.")
    print("Render OG PNGs with: ./gen_og_cards.sh")


if __name__ == "__main__":
    main()
