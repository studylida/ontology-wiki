import urllib.request
import urllib.parse
import re
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

search_terms = ['반도체 용어 사전', '용어사전 웨이퍼', '용어사전 수율', '용어사전 EUV', '용어사전 클린룸']
found_posts = {}

for term in search_terms:
    url = f"https://news.samsungsemiconductor.com/kr/?s={urllib.parse.quote(term)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        matches = re.findall(r'<a\s+[^>]*href=[\"\'](https://news\.samsungsemiconductor\.com/kr/[^\"\']+)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
        for link, text in matches:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            if ('용어' in clean_text or '사전' in clean_text or '공정' in clean_text) and len(clean_text) > 8:
                decoded_link = urllib.parse.unquote(link)
                found_posts[decoded_link] = clean_text
    except Exception as e:
        print(f"Error searching {term}: {e}")

print(f"Total relevant glossary posts found: {len(found_posts)}")
for link, title in list(found_posts.items())[:25]:
    # take first line of title
    t_first = title.split('\n')[0].strip()
    print(f" - {t_first} -> {link}")
