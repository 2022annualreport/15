import os
import random
from datetime import datetime

# مجلد نشر الفيديوهات
BASE_DIR = 'now/videos/'

# كلمات المفتاحية
keywords = {
    "global": [
        "sex xnxx",
        "xxx porn",
        "hot sexvideo",
        "viral sex scandal",
        "trending porn video"
    ],
    "arabic": [
        "سكس فضيحة",
        "سكس xnxx",
        "نيك نار",
        "سكس ترند",
        "فيديو سكس ساخن"
    ]
}

# كلمات عامة إضافية
general_words = ["porn", "xxx", "sex", "adult", "hot video", "hd video",
                 "trending", "popular", "watch online",
                 "سكس", "سكس عربي", "سكس مصري", "سكس مترجم",
                 "سكس نودز", "سكس عراقي", "نيك", "نيك عربي"]

# دالة لإنشاء منشور

def create_post():
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    filename = f'post_{timestamp}.html'
    filepath = os.path.join(BASE_DIR, filename)

    # اختيار عنوان ووصف عشوائي
    title = random.choice(general_words + keywords['global'] + keywords['arabic'])
    description = random.choice(general_words + keywords['global'] + keywords['arabic'])

    # إنشاء محتوى HTML مع سكيما فيديو
    html_content = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "{title}",
  "description": "{description}",
  "thumbnailUrl": "https://example.com/thumbnail.jpg",
  "uploadDate": "{now.isoformat()}",
  "contentUrl": "https://example.com/videos/{filename}",
  "embedUrl": "https://example.com/videos/{filename}"
}}
</script>
</head>
<body>
<h1>{title}</h1>
<p>{description}</p>
<video controls src="https://example.com/videos/{filename}"></video>
</body>
</html>'''

    # كتابة الملف
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f'تم إنشاء المنشور: {filename}')


# مثال على إنشاء منشور واحد
create_post()
