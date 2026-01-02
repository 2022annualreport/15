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

# كلمات مفتاحية إضافية لتحسين التنوع
GLOBAL_KEYWORDS = [
    "trending", "popular", "watch online", "hd video",
    "سكس", "سكس عربي", "سكس مصري", "سكس مترجم",
    "سكس نودز", "سكس عراقي", "نيك", "نيك عربي"
]

# ============================
# أدوات مساعدة
# ============================

def slugify(text: str) -> str:
    """تحويل النص لروابط صديقة لمحركات البحث مع دعم العربية"""
    text = text.strip().lower()
    # استبدال المسافات والرموز بشرطة، مع الحفاظ على الحروف العربية
    text = re.sub(r"[^\w\u0600-\u06FF]+", "-", text)
    return text.strip("-")

def load_trends(path: str = "trending_keywords.json") -> List[str]:
    """تحميل الكلمات المفتاحية من ملف JSON"""
    if not os.path.exists(path):
        print(f"Error: {path} not found.")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        words = []
        # جمع الكلمات من كافة التصنيفات (global, arabic, إلخ)
        for category in data.values():
            if isinstance(category, list):
                for w in category:
                    if len(str(w)) >= 3:
                        words.append(str(w))
        random.shuffle(words)
        return words
    except Exception as e:
        print(f"JSON Load Error: {e}")
        return []

def choose_batch(words: List[str]) -> List[str]:
    """اختيار عدد عشوائي من الكلمات للنشر في هذه الدفعة"""
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
<style>
    body { font-family: sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: auto; }
    h1 { color: #333; }
    ul { list-style: none; padding: 0; }
    li { margin-bottom: 10px; }
    a { color: #007bff; text-decoration: none; }
    a:hover { text-decoration: underline; }
</style>
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
<footer><p>© {{ year }} - جميع الحقوق محفوظة</p></footer>
</body>
</html>"""

def build_page(keyword: str, all_slugs: List[str]):
    """بناء محتوى الصفحة والروابط الداخلية"""
    mix = random.sample(GLOBAL_KEYWORDS, k=min(4, len(GLOBAL_KEYWORDS)))
    title = f"{keyword} - مشاهدة فيديو {', '.join(mix)}"
    description = f"استمتع بمشاهدة {keyword} بجودة عالية. نوفر لك أحدث مقاطع {', '.join(mix)} الحصرية والمتجددة يومياً."
    
    clean_keyword = slugify(keyword)
    # إضافة طابع زمني مصغر لضمان عدم تكرار الملفات أبداً
    unique_suffix = datetime.now().strftime("%S%f")[:4]
    slug = f"{clean_keyword}-{unique_suffix}" 
    canonical = f"{SITE_CANONICAL}/{OUTPUT_DIR}/{slug}.html"

    anchors = []
    # اختيار روابط داخلية ذكية (تجنب الروابط الفارغة)
    if all_slugs:
        sample_size = min(len(all_slugs), 8)
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
        block_title=random.choice(["فيديوهات ذات صلة", "اكتشف المزيد", "مقاطع مختارة لك"]),
        anchors=anchors,
        year=datetime.utcnow().year
    )
    return slug, html

# ============================
# الرفع وجلب الملفات من GitHub
# ============================

def get_existing_slugs(repo):
    """جلب قائمة الملفات الحالية من GitHub لتحديث الروابط الداخلية"""
    try:
        # نحاول جلب قائمة الملفات من المجلد المحدد
        contents = repo.get_contents(OUTPUT_DIR)
        return [os.path.splitext(c.name)[0] for c in contents if c.name.endswith('.html')]
    except Exception as e:
        print(f"Note: Could not fetch existing files (this is normal on first run): {e}")
        return []

def push_files(pages, repo):
    """رفع الملفات الجديدة إلى المستودع"""
    for slug, html in pages:
        path = f"{OUTPUT_DIR}/{slug}.html"
        try:
            try:
                # التحقق إذا كان الملف موجوداً لتحديثه
                existing = repo.get_contents(path)
                repo.update_file(path, f"Update content: {slug}", html, existing.sha)
                print(f"Successfully updated: {path}")
            except:
                # إنشاء ملف جديد إذا لم يكن موجوداً
                repo.create_file(path, f"Publish new page: {slug}", html)
                print(f"Successfully created: {path}")
            time.sleep(1) # تأخير لتفادي حظر API الخاص بـ GitHub
        except Exception as e:
            print(f"Error pushing {slug}: {e}")

if __name__ == "__main__":
    # التحقق من وجود المتغيرات الضرورية
    if not GITHUB_TOKEN or not REPO_NAME:
        print("CRITICAL ERROR: GITHUB_TOKEN or REPO_NAME is not set in environment.")
        exit(1)

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to connect to GitHub: {e}")
        exit(1)

    trends = load_trends()
    if not trends:
        print("No trending keywords found. Exiting.")
        exit(0)

    # جلب أسماء الملفات القديمة لعمل الروابط الداخلية
    existing_slugs = get_existing_slugs(repo)
    print(f"Database contains {len(existing_slugs)} existing pages.")

    batch = choose_batch(trends)
    print(f"Selected batch: {batch}")
    
    pages_to_upload = []

    for kw in batch:
        slug, html = build_page(kw, existing_slugs)
        pages_to_upload.append((slug, html))
        # تحديث القائمة محلياً ليتم الربط بين ملفات الدفعة الواحدة أيضاً
        existing_slugs.append(slug)

    # تنفيذ عملية الرفع
    push_files(pages_to_upload, repo)
    print(f"Job finished. {len(pages_to_upload)} pages published successfully.")
