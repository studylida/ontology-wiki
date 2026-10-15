import urllib.request
import re
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://news.samsungsemiconductor.com/kr/?s=8%EB%8C%80+%EA%B3%B5%EC%A0%95'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

# Find article links
articles = re.findall(r'<a\s+[^>]*href=[\"\'](https://news\.samsungsemiconductor\.com/kr/[^\"\']+)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
print(f'Found {len(articles)} links in search results:')
seen = set()
for link, text in articles:
    clean_text = re.sub(r'<[^>]+>', '', text).strip()
    if link not in seen and clean_text:
        seen.add(link)
        print(f' - {clean_text} -> {link}')
