import urllib.request
import re
import ssl
import sys
import urllib.parse


sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_category_articles(cat_slug):
    articles = []
    page = 1
    while True:
        # url
        if page == 1:
            url = f'https://news.samsungsemiconductor.com/kr/category/기술/{cat_slug}/'
        else:
            url = f'https://news.samsungsemiconductor.com/kr/category/기술/{cat_slug}/page/{page}/'
        
        encoded_url = urllib.parse.quote(url, safe=':/?&=#')
        try:
            req = urllib.request.Request(encoded_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            # 404 means no more pages
            break
        
        # Parse post titles and links
        # Looking for <h2 class="entry-title"><a href="...">...</a></h2> or similar
        links = re.findall(r'<a\s+[^>]*href=[\"\'](https://news\.samsungsemiconductor\.com/kr/[^\"\']+)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
        found_in_page = 0
        for link, text in links:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            # If link has title and is an actual article
            if ('/category/' not in link and '/sp/' not in link and '/page/' not in link and
                len(clean_text) > 5 and not any(k in clean_text for k in ['개인정보', '뉴스룸 소개', '운영원칙', '자세히보기'])):
                decoded_link = urllib.parse.unquote(link)
                if not any(a['url'] == decoded_link for a in articles):
                    articles.append({'title': clean_text, 'url': decoded_link})
                    found_in_page += 1
        
        print(f'Category [{cat_slug}] Page {page}: found {found_in_page} articles. Total: {len(articles)}')
        if found_in_page == 0 or page >= 10:  # safety break
            break
        page += 1
    return articles

print('=== Crawling 8대 공정 Category ===')
eight_processes = fetch_category_articles('8대-공정')
for i, a in enumerate(eight_processes, 1):
    print(f"{i:2d}. {a['title']} -> {a['url']}")

print('\n=== Crawling 용어사전 Category (First 30) ===')
glossary = fetch_category_articles('용어사전')
for i, a in enumerate(glossary[:30], 1):
    print(f"{i:2d}. {a['title']} -> {a['url']}")
print(f'Total glossary articles: {len(glossary)}')
