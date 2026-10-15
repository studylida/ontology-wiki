import urllib.request
import urllib.parse
import re
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

articles = []
for page in range(11, 35):
    url = f'https://news.samsungsemiconductor.com/kr/category/기술/용어사전/page/{page}/'
    encoded_url = urllib.parse.quote(url, safe=':/?&=#')
    try:
        req = urllib.request.Request(encoded_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"End of pages at page {page} ({e})")
        break
    
    links = re.findall(r'<a\s+[^>]*href=[\"\'](https://news\.samsungsemiconductor\.com/kr/[^\"\']+)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
    cnt = 0
    for link, text in links:
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        if ('/category/' not in link and '/sp/' not in link and '/page/' not in link and
            len(clean_text) > 5 and not any(k in clean_text for k in ['개인정보', '뉴스룸 소개', '운영원칙', '자세히보기'])):
            decoded_link = urllib.parse.unquote(link)
            if not any(a['url'] == decoded_link for a in articles):
                articles.append({'title': clean_text, 'url': decoded_link, 'page': page})
                cnt += 1
    print(f"Page {page}: found {cnt} articles.")

print(f"\nTotal older glossary articles found: {len(articles)}")
for a in articles[:30]:
    t_clean = a['title'].split('\n')[0].strip()
    print(f" - [{a['page']}] {t_clean} -> {a['url']}")
