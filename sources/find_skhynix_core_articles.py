import urllib.request
import urllib.parse
import re
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

queries = ['식각', 'MR-MUF', '전공정', '후공정', '8대 공정']
links_dict = {}

for q in queries:
    url = f"https://news.skhynix.co.kr/?s={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        matches = re.findall(r'<a\s+[^>]*href=[\"\'](https://news\.skhynix\.co\.kr/([a-zA-Z0-9\-_%]+)/?)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
        for full, slug, t in matches:
            if slug not in ['category', 'tag', 'about', 'contact', 'en', 'cn', 'fact', 'press', 'story', 'ir']:
                ct = re.sub(r'<[^>]+>', '', t).strip()
                ct = re.sub(r'\s+', ' ', ct)
                if len(ct) > 6 and not any(k in ct for k in ['Read Post', '개인정보', '이메일']):
                    links_dict[full] = ct
    except Exception as e:
        print(f"Error {q}: {e}")

print(f"Found {len(links_dict)} articles for core process keywords:")
for l, t in list(links_dict.items()):
    if any(k in t for k in ['식각', 'MR-MUF', '공정', 'MUF', 'HBM', '패키징', '본딩', 'TSV']):
        print(f" - {t[:55]} -> {l}")
