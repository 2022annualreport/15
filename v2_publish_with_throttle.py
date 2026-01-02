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
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = os.getenv("REPO_NAME") 
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
    slug = f"{clean_keyword}-{random.randint(1000,9999)}" # تم زيادة الرقم العشوائي لتجنب التكرار
    canonical = f"{SITE_CANONICAL}/{OUTPUT_DIR}/{slug}.html"

    anchors = []
    # اختيار عشوائي من الروابط الموجودة للربط الداخلي
    if all_slugs:
        sample_size = min(len(all_slugs), 10)
        pool = random.sample(all_slugs, k=sample_size)
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
# الرفع وجلب الملفات من GitHub
# ============================

def get_existing_slugs(repo):
    """جلب قائمة الملفات الموجودة حالياً في المستودع"""
    try:
        contents = repo.get_contents(OUTPUT_DIR)
        return [os.path.splitext(c.name)[0] for c in contents if c.name.endswith('.html')]
    except:
        return []

def push_files(pages, repo):
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
            time.sleep(1) # تأخير بسيط لتجنب الـ Rate Limit
        except Exception as e:
            print(f"Failed to push {slug}: {e}")

if __name__ == "__main__":
    if not GITHUB_TOKEN or not REPO_NAME:
        print("Missing environment variables.")
        exit(1)

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    trends = load_trends()
    if not trends:
        print("No keywords found.")
        exit(0)

    # جلب الروابط القديمة من المستودع فعلياً
    existing_slugs = get_existing_slugs(repo)
    print(f"Found {len(existing_slugs)} existing pages.")

    batch = choose_batch(trends)
    pages_to_upload = []

    for kw in batch:
        slug, html = build_page(kw, existing_slugs)
        pages_to_upload.append((slug, html))
        # إضافة الرابط الجديد للقائمة لكي تستفيد منه الصفحات التالية في نفس الدفعة
        existing_slugs.append(slug)

    push_files(pages_to_upload, repo)
    print(f"Done. Processed {len(pages_to_upload)} keywords.")
