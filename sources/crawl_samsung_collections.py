import urllib.request
import re
import ssl
import sys
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    'https://news.samsungsemiconductor.com/kr/%EB%B0%98%EB%8F%84%EC%B2%B4-%EB%B0%B1%EA%B3%BC%EC%82%AC%EC%A0%84-%EB%AA%A8%EC%95%84%EB%B3%B4%EA%B8%B0/',
    'https://news.samsungsemiconductor.com/kr/%EB%B0%98%EB%8F%84chat/'
]

for url in urls:
    print(f'=== FETCHING: {url} ===')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        # Find links
        links = re.findall(r'<a\s+[^>]*href=[\"\'](https://news\.samsungsemiconductor\.com/kr/[^\"\']+)[\"\'][^>]*>(.*?)</a>', html, re.DOTALL)
        print(f'Found {len(links)} links:')
        seen = set()
        for link, text in links:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            # filter out common nav links
            if link not in seen and clean_text and len(clean_text) > 3 and not any(k in clean_text for k in ['개인정보', '뉴스룸 소개', '운영원칙']):
                seen.add(link)
                # decode url for readable output
                decoded_url = urllib.parse.unquote(link)
                print(f'  [{clean_text}] -> {decoded_url}')
    except Exception as e:
        print(f'Error fetching {url}: {e}')
