# Taco Week

A static recreation of the [Taco Week](https://medium.com/taco-week) Medium
publication — *"It's like shark week, but for tacos."* Six illustrated posts
from September 2015, rebuilt as a dependency-free static site you can host
anywhere (Netlify, Vercel, GitHub Pages, Cloudflare Pages, S3, …).

## Structure

```
raw/feed.xml       Archived Medium RSS feed (source of truth for post content)
raw/posts.json     Parsed posts, ordered chronologically (day 1 → day 6)
build.py           Transforms posts.json into the static site
gen_og_cards.sh    Renders the social-share cards (needs agent-browser)
_ogcards/          Generated HTML templates for the social cards (not deployed)
public/            The built site — this is what you deploy
  index.html       Landing page with the post grid
  *.html           One page per taco post
  style.css        All styling
  robots.txt       Allows all crawlers, points to the sitemap
  sitemap.xml      Lists every page
  images/          Illustrations (Laura Bohill), logo, author avatar
  images/og/       1200×630 Open Graph / Twitter social cards (one per page)
```

Each page ships SEO + social metadata: a unique title and description, a
canonical URL, Open Graph and Twitter Card tags pointing at a per-page social
image, and JSON-LD structured data (`Article` on posts, `Blog` + `ItemList`
on the home page). HTML validates clean against the W3C Nu checker.

## Build

```sh
python3 build.py        # regenerate all HTML, sitemap.xml, robots.txt
./gen_og_cards.sh       # re-render the 1200×630 social cards (optional)
```

`build.py` has no dependencies — just Python 3. `gen_og_cards.sh` uses
`agent-browser` (headless Chrome) to screenshot the card templates; if it's
not installed the step is skipped and the existing card PNGs are kept.

> **Note:** the production origin is set in `build.py` as `BASE_URL =
> "https://tacoweek.com"`. Change it there if you host on a different domain,
> then rebuild so canonical/OG URLs stay correct.

## Preview locally

```sh
cd public && python3 -m http.server 8000
# open http://localhost:8000
```

## Deploy

Upload the contents of `public/` to any static host. The site uses relative
links throughout, so it works from a domain root or a subpath.

## Editing posts

Post content lives in `raw/posts.json`. Edit the `content` HTML there and
re-run `build.py`, or edit the generated `public/*.html` directly if you no
longer need to rebuild.

## Credits

Words by Alex Baldwin. Illustrations by [Laura Bohill](https://twitter.com/LauRARbee). 2015.
