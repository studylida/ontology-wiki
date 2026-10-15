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

out_dir = r'c:\Users\BISTelligence\ontology-wiki\sources\lam_research'
os.makedirs(out_dir, exist_ok=True)

solution_articles = [
    {
        'id': 'lam_solution_etch_kr',
        'title': '램리서치 식각(Etch) 솔루션 총론 (한국어)',
        'url': 'https://www.lamresearch.com/ko/technology-solutions/etch/'
    },
    {
        'id': 'lam_solution_deposition_kr',
        'title': '램리서치 증착(Deposition) 솔루션 총론 (한국어)',
        'url': 'https://www.lamresearch.com/ko/technology-solutions/deposition/'
    },
    {
        'id': 'lam_solution_etch_en',
        'title': 'Lam Research Etch Technology Solutions (Global)',
        'url': 'https://www.lamresearch.com/technology-solutions/etch/'
    },
    {
        'id': 'lam_solution_deposition_en',
        'title': 'Lam Research Deposition Technology Solutions (Global)',
        'url': 'https://www.lamresearch.com/technology-solutions/deposition/'
    }
]

def clean_html(raw_html):
    # Remove script, style, header, footer
    body = re.sub(r'<script[^>]*>.*?</script>', '', raw_html, flags=re.DOTALL)
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    body = re.sub(r'<header[^>]*>.*?</header>', '', body, flags=re.DOTALL)
    body = re.sub(r'<footer[^>]*>.*?</footer>', '', body, flags=re.DOTALL)
    body = re.sub(r'<nav[^>]*>.*?</nav>', '', body, flags=re.DOTALL)

    body = re.sub(r'<h[1-4][^>]*>(.*?)</h[1-4]>', r'\n### \1\n', body, flags=re.DOTALL)
    body = re.sub(r'<br\s*/?>', '\n', body)
    body = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', body, flags=re.DOTALL)
    body = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', body, flags=re.DOTALL)
    body = re.sub(r'<(?:strong|b)>(.*?)</(?:strong|b)>', r'**\1**', body, flags=re.DOTALL)
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

for item in solution_articles:
    file_path = os.path.join(out_dir, f"{item['id']}.md")
    print(f"Downloading: {item['title']}...")
    try:
        req = urllib.request.Request(item['url'], headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            raw_html = resp.read().decode('utf-8', errors='ignore')
        
        md_text = clean_html(raw_html)
        header = f"""---
title: "{item['title']}"
source_url: "{item['url']}"
publisher: "Lam Research"
source_id: "{item['id']}"
type: "official_technology_solution"
---

# {item['title']}

"""
        full_content = header + md_text
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        print(f"  -> Saved {len(full_content):,} characters to {os.path.basename(file_path)}")
    except Exception as e:
        print(f"  -> Error: {e}")

print("Solution articles saved successfully!")
