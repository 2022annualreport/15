name: Hourly Publisher

on:
schedule:
- cron: '0 * * * *'
workflow_dispatch:

jobs:
publish:
runs-on: ubuntu-latest
# إضافة الصلاحيات ضرورية للسماح للأكشن بالكتابة في المستودع
permissions:
contents: write
steps:
- name: Checkout
uses: actions/checkout@v4
with:
fetch-depth: 0

  - name: Set up Python
    uses: actions/setup-python@v5
    with:
      python-version: '3.11'

  - name: Install deps
    run: |
      pip install jinja2 PyGithub pandas

  - name: Run publisher
    env:
      # استخدم التوكن التلقائي الذي يوفره GitHub Actions
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      # تأكد من وضع اسم المستودع الصحيح هنا (مثال: user/repo)
      REPO_NAME: ${{ github.repository }}
    run: |
      python v2_publish_with_throttle.py
