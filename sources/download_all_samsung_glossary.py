import urllib.request
import urllib.parse
import re
import os
import ssl
import sys
import html

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

out_dir = r'c:\Users\BISTelligence\ontology-wiki\sources\samsung\glossary'
os.makedirs(out_dir, exist_ok=True)

# First get all glossary links from page 11 to 23
glossary_items = []
for page in range(11, 25):
    url = f'https://news.samsungsemiconductor.com/kr/category/기술/용어사전/page/{page}/'
    encoded_url = urllib.parse.quote(url, safe=':/?&=#')
    try:
        req = urllib.request.Request(encoded_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            page_html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        break
    
    links = re.findall(r'<a\s+[^>]*href=[\"\'](https://news\.samsungsemiconductor\.com/kr/[^\"\']+)[\"\'][^>]*>(.*?)</a>', page_html, re.DOTALL)
    for link, text in links:
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        if ('/category/' not in link and '/sp/' not in link and '/page/' not in link and
            len(clean_text) > 5 and not any(k in clean_text for k in ['개인정보', '뉴스룸 소개', '운영원칙', '자세히보기'])):
            decoded_link = urllib.parse.unquote(link)
            if not any(a['url'] == decoded_link for a in glossary_items):
                # slug
                slug = decoded_link.strip('/').split('/')[-1]
                glossary_items.append({'title': clean_text.split('\n')[0].strip(), 'url': decoded_link, 'slug': slug})

print(f"Found total {len(glossary_items)} official Samsung Glossary items. Downloading to {out_dir}...")

def clean_html_to_markdown(raw_html):
    content_match = re.search(r'<div class="entry-content[^"]*">(.*?)</div>\s*<!-- \.entry-content -->', raw_html, re.DOTALL)
    if not content_match:
        content_match = re.search(r'<div class="entry-content[^"]*">(.*?)</article>', raw_html, re.DOTALL)
    body = content_match.group(1) if content_match else raw_html

    body = re.sub(r'<h[1-4][^>]*>(.*?)</h[1-4]>', r'\n### \1\n', body, flags=re.DOTALL)
    body = re.sub(r'<br\s*/?>', '\n', body)
    body = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', body, flags=re.DOTALL)
    body = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', body, flags=re.DOTALL)
    body = re.sub(r'<(?:strong|b)>(.*?)</(?:strong|b)>', r'**\1**', body, flags=re.DOTALL)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    body = re.sub(r'<[^>]+>', '', body)
    body = html.unescape(body)

    lines = [line.strip() for line in body.split('\n')]
    cleaned = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned.append('')
                prev_empty = True
        else:
            cleaned.append(line)
            prev_empty = False
    return '\n'.join(cleaned).strip()

downloaded = 0
for item in glossary_items:
    safe_slug = re.sub(r'[\\/*?:"<>|]', '_', item['slug'])
    file_path = os.path.join(out_dir, f"{safe_slug}.md")
    if os.path.exists(file_path):
        continue
    try:
        encoded_url = urllib.parse.quote(item['url'], safe=':/?&=#')
        req = urllib.request.Request(encoded_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            raw_html = resp.read().decode('utf-8', errors='ignore')
        
        md_text = clean_html_to_markdown(raw_html)
        header = f"""---
title: "{item['title']}"
source_url: "{item['url']}"
publisher: "Samsung Semiconductor"
type: "official_glossary_term"
---

# {item['title']}

"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header + md_text)
        downloaded += 1
        if downloaded % 10 == 0:
            print(f"Downloaded {downloaded}/{len(glossary_items)} terms...")
    except Exception as e:
        print(f"Error {item['slug']}: {e}")

print(f"Finished! Successfully saved {downloaded} glossary files to {out_dir}")
