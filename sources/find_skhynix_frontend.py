import urllib.request
import urllib.parse
import re
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://news.skhynix.co.kr/?s=%EB%B0%98%EB%8F%84%EC%B2%B4+%EC%A0%84%EA%B3%B5%EC%A0%95"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    matches = re.findall(r'<a\s+[^>]*href=[\"\'](https://news\.skhynix\.co\.kr/([a-zA-Z0-9\-_%]+)/?)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
    seen = set()
    print("Found Front-end Process Series:")
    for full, slug, t in matches:
        if slug not in ['category', 'tag', 'about', 'contact', 'en', 'cn', 'fact', 'press', 'story', 'ir']:
            ct = re.sub(r'<[^>]+>', '', t).strip()
            ct = re.sub(r'\s+', ' ', ct)
            if full not in seen and len(ct) > 5 and not any(k in ct for k in ['Read Post', '개인정보']):
                seen.add(full)
                print(f" - {ct} -> {full}")
except Exception as e:
    print(f"Error: {e}")
