import urllib.request
import urllib.parse
import re
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Query TECH&AI category pages and specific technical search terms
targets = [
    'https://news.skhynix.co.kr/category/tech-and-ai/',
    'https://news.skhynix.co.kr/category/tech-and-ai/page/2/',
    'https://news.skhynix.co.kr/category/tech-and-ai/page/3/',
    'https://news.skhynix.co.kr/?s=%EC%8B%9D%EA%B0%81',
    'https://news.skhynix.co.kr/?s=MR-MUF',
    'https://news.skhynix.co.kr/?s=TSV',
    'https://news.skhynix.co.kr/?s=HBM',
    'https://news.skhynix.co.kr/?s=%ED%95%98%EC%9D%B4%ED%94%BC%EB%94%94%EC%95%84',
    'https://news.skhynix.co.kr/?s=%ED%8C%A8%ED%82%A4%EC%A7%95'
]

found = {}

for u in targets:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            
            # Match links like https://news.skhynix.co.kr/<slug>/
            links = re.findall(r'<a\s+[^>]*href=[\"\'](https://news\.skhynix\.co\.kr/([a-zA-Z0-9\-_%]+)/?)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
            for full_url, slug, text in links:
                if slug in ['category', 'tag', 'about', 'contact', 'en', 'cn', 'fact', 'press', 'story', 'ir']:
                    continue
                clean_text = re.sub(r'<[^>]+>', '', text).strip()
                clean_text = re.sub(r'\s+', ' ', clean_text)
                if len(clean_text) > 8 and not any(k in clean_text for k in ['Read Post', '개인정보', '이메일', '공지사항']):
                    if full_url not in found:
                        found[full_url] = clean_text
    except Exception as e:
        print(f"Error {u}: {e}")

print(f"Found {len(found)} SK hynix technical articles:")
for u, t in list(found.items())[:35]:
    print(f" - {t[:50]} -> {u}")
