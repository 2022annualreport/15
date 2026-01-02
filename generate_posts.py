import os
import random
from datetime import datetime

BASE_DIR = 'now/videos/'

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

general_words = ["porn", "xxx", "sex", "adult", "hot video", "hd video",
                 "trending", "popular", "watch online",
                 "سكس", "سكس عربي", "سكس مصري", "سكس مترجم",
                 "سكس نودز", "سكس عراقي", "نيك", "نيك عربي"]

def create_post():
    now = datetime.now()
    timestamp = now.strftime('%Y%m%d%H%M%S')
    filename = f'post_{timestamp}.html'
    filepath = os.path.join(BASE_DIR, filename)

    title = random.choice(general_words + keywords['global'] + keywords['arabic'])
    description = random.choice(general_words + keywords['global'] + keywords['arabic'])

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

    # إنشاء المجلد بأمان
    if not os.path.isdir(BASE_DIR):
        if os.path.exists(BASE_DIR):
            os.remove(BASE_DIR)
        os.makedirs(BASE_DIR)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f'تم إنشاء المنشور: {filename}')

create_post()
