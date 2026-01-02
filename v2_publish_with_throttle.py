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
# إعدادات أساسية (تُقرأ من البيئة)
# ============================
# لا تضع التوكن هنا أبداً! سيقوم GitHub بتعطيله فوراً.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME") # يقرأ تلقائياً من Workflow
SITE_CANONICAL = "https://tgf-cluster.docs.stord.com"
OUTPUT_DIR = "now/videos"

PAGES_PER_RUN_MIN = 3
PAGES_PER_RUN_MAX = 7
GA_MEASUREMENT_ID = "G-3L7L7QN2RW"

GLOBAL_KEYWORDS = [
    "trending", "popular", "watch online", "hd video",
    "سكس", "سكس عربي", "سكس مصري", "سكس مترجم",
    "سكس نودز", "سكس عراقي", "نيك", "نيك عربي"
]

# ============================
# أدوات مساعدة
# ============================

def slugify(text: str) -> str:
    # تحويل النص لرابط متوافق
    text = text.strip().lower()
    text = re.sub(r"[^\w\u0600-\u06FF]+", "-", text)
    return text.strip("-")

def load_trends(path: str = "trending_keywords.json") -> List[str]:
    if not os.path.exists(path):
        print(f"Error: {path} not found.")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        words = []
        for arr in data.values():
            for w in arr:
                if len(w) >= 3:
                    words.append(w)
        random.shuffle(words)
        return words
    except Exception as e:
        print(f"JSON Load Error: {e}")
        return []

def choose_batch(words: List[str]) -> List[str]:
    if not words: return []
    n = random.randint(PAGES_PER_RUN_MIN, PAGES_PER_RUN_MAX)
    return words[:n]

# ============================
# قالب HTML
# ============================
TEMPLATE = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8"/>
<title>{{ title }}</title>
<meta name="description" content="{{ description }}">
<link rel="canonical" href="{{ canonical }}"/>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script async src="https://www.googletagmanager.com/gtag/js?id={{ ga_id }}"></script>
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
    <li><a href="{{ a.href }}">{{ a.text }}</a></li>
    {% endfor %}
  </ul>
</section>
<footer><p>© {{ year }}</p></footer>
</body>
</html>"""

def build_page(keyword: str, all_slugs: List[str]):
    mix = random.sample(GLOBAL_KEYWORDS, k=min(4, len(GLOBAL_KEYWORDS)))
    title = f"{keyword} فيديو سكس {', '.join(mix)}"
    description = f"مشاهدة {keyword} بجودة عالية {', '.join(mix)} فيديوهات رائجة."
    
    clean_keyword = slugify(keyword)
    slug = f"{clean_keyword}-{random.randint(100,999)}"
    canonical = f"{SITE_CANONICAL}/{OUTPUT_DIR}/{slug}.html"

    anchors = []
    pool = all_slugs[-10:] # ربط بآخر 10 صفحات تم إنشاؤها
    for s in pool:
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
        block_title=random.choice(["قد يعجبك أيضاً", "مشاهدة المزيد", "مقاطع شائعة"]),
        anchors=anchors,
        year=datetime.utcnow().year
    )
    return slug, html

# ============================
# الرفع إلى GitHub
# ============================

def push_files(pages):
    if not GITHUB_TOKEN or not REPO_NAME:
        print("Missing GITHUB_TOKEN or REPO_NAME environment variables.")
        return

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    for slug, html in pages:
        path = f"{OUTPUT_DIR}/{slug}.html"
        try:
            try:
                existing = repo.get_contents(path)
                repo.update_file(path, f"Update {slug}", html, existing.sha)
                print(f"Updated: {path}")
            except:
                repo.create_file(path, f"Add {slug}", html)
                print(f"Created: {path}")
            time.sleep(0.5)
        except Exception as e:
            print(f"Failed to push {slug}: {e}")

if __name__ == "__main__":
    # تأكد من وجود المجلد محلياً (للأكشن)
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    trends = load_trends()
    if not trends:
        print("No keywords found.")
        exit(0)

    batch = choose_batch(trends)
    
    # محاكاة السجلات السابقة للربط الداخلي
    existing_slugs = [] 
    pages_to_upload = []

    for kw in batch:
        slug, html = build_page(kw, existing_slugs)
        pages_to_upload.append((slug, html))
        existing_slugs.append(slug)

    push_files(pages_to_upload)
    print(f"Done. Processed {len(pages_to_upload)} keywords.")
