# v2_publish_with_throttle.py (FIXED VERSION)
# نشر تدريجي + ربط داخلي + GitHub Actions جاهز

import os
import json
import random
import re
import time
from datetime import datetime
from typing import List
from jinja2 import Environment, BaseLoader
from github import Github

# ============================
# إعدادات أساسية (عدّل هذه فقط)
# ============================
GITHUB_TOKEN = os.getenv("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") or "PUT_YOUR_TOKEN_HERE"
REPO_NAME = "2022annualreport/15"
SITE_CANONICAL = "https://tgf-cluster.docs.stord.com"
OUTPUT_DIR = "now/videos"

PAGES_PER_RUN_MIN = 3
PAGES_PER_RUN_MAX = 7

GA_MEASUREMENT_ID = "G-3L7L7QN2RW"

GLOBAL_KEYWORDS = [
    "porn", "xxx", "sex", "adult", "hot video", "hd video",
    "trending", "popular", "watch online",
    "سكس", "سكس عربي", "سكس مصري", "سكس مترجم",
    "سكس نودز", "سكس عراقي", "نيك", "نيك عربي"
]

# ============================
# أدوات مساعدة
# ============================

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\u0600-\u06FF]+", "-", text)
    return text.strip("-")


def load_trends(path: str = "trending_keywords.json") -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    words = []
    for arr in data.values():
        for w in arr:
            if len(w) >= 3:
                words.append(w)
    random.shuffle(words)
    return words


def choose_batch(words: List[str]) -> List[str]:
    if not words:
        return []
    n = random.randint(PAGES_PER_RUN_MIN, PAGES_PER_RUN_MAX)
    return words[:n]

# ============================
# قالب HTML (مُصحّح)
# ============================
TEMPLATE = """<!DOCTYPE html>
<html dir=\"rtl\" lang=\"ar\">
<head>
<meta charset=\"utf-8\"/>
<title>{{ title }}</title>
<meta name=\"description\" content=\"{{ description }}\">
<link rel=\"canonical\" href=\"{{ canonical }}\"/>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<script async src=\"https://www.googletagmanager.com/gtag/js?id={{G-3L7L7QN2RW}}\"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);} gtag('js', new Date());
  gtag('config', '{{ ga_id }}');
</script>
</head>
<body>
<h1>{{ title }}</h1>
<p>{{ description }}</p>

<section>
  <h2>{{ block_title }}</h2>
  <ul>
    {% for a in anchors %}
    <li><a href=\"{{ a.href }}\">{{ a.text }}</a></li>
    {% endfor %}
  </ul>
</section>

<footer>
  <p>© {{ year }}</p>
</footer>
</body>
</html>"""

# ============================
# منطق التوليد
# ============================

def build_page(keyword: str, all_slugs: List[str]):
    mix = random.sample(GLOBAL_KEYWORDS, k=min(4, len(GLOBAL_KEYWORDS)))
    title = f"{keyword} فيديو سكس {', '.join(mix)}"
    description = f"مشاهدة {keyword} بجودة عالية {', '.join(mix)} فيديوهات سكس رائجة ومحدثة باستمرار."

    slug = slugify(f"{keyword}-{'-'.join(mix)}")
    canonical = f"{SITE_CANONICAL}/{OUTPUT_DIR}/{slug}.html"

    pool = [s for s in all_slugs if s != slug]
    random.shuffle(pool)
    anchors = []
    for s in pool[:5]:
        anchors.append({
            "href": f"{SITE_CANONICAL}/{OUTPUT_DIR}/{s}.html",
            "text": s.replace('-', ' ')
        })

    env = Environment(loader=BaseLoader())
    tpl = env.from_string(TEMPLATE)
    html = tpl.render(
        title=title,
        description=description,
        canonical=canonical,
        ga_id=GA_MEASUREMENT_ID,
        block_title=random.choice(["قد يعجبك أيضًا", "مشاهدة المزيد", "مقاطع شائعة"]),
        anchors=anchors,
        year=datetime.utcnow().year
    )
    return slug, html

# ============================
# GitHub رفع
# ============================

def push_files(pages):
    g = Github(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)
    repo = g.get_repo(15)

    for slug, html in pages:
        path = f"{OUTPUT_DIR}/{slug}.html"
        try:
            existing = repo.get_contents(path)
            repo.update_file(existing.path, f"update {slug}", html, existing.sha)
        except Exception:
            repo.create_file(path, f"add {slug}", html)
        time.sleep(1)

# ============================
# تشغيل
# ============================
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    trends = load_trends()
    if not trends:
        print("No trending keywords found.")
        exit(0)

    batch = choose_batch(trends)

    existing_slugs = []
    for root, _, files in os.walk(OUTPUT_DIR):
        for f in files:
            if f.endswith('.html'):
                existing_slugs.append(os.path.splitext(f)[0])

    pages = []
    for kw in batch:
        slug, html = build_page(kw, existing_slugs)
        with open(os.path.join(OUTPUT_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(html)
        pages.append((slug, html))
        existing_slugs.append(slug)

    push_files(pages)
    print(f"Published {len(pages)} pages to {OUTPUT_DIR}")
