import urllib.request
import re
import os
import ssl
import sys
import html

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

amat_dir = r'c:\Users\BISTelligence\ontology-wiki\sources\amat'
semi_dir = r'c:\Users\BISTelligence\ontology-wiki\sources\semi'
os.makedirs(amat_dir, exist_ok=True)
os.makedirs(semi_dir, exist_ok=True)

# 1. AMAT Core Solutions
amat_targets = [
    {
        'id': 'amat_cmp_planarization',
        'title': 'Chemical Mechanical Planarization (CMP) Solutions',
        'url': 'https://www.appliedmaterials.com/us/en/semiconductor/products/cmp.html'
    },
    {
        'id': 'amat_epitaxy_transistor',
        'title': 'Epitaxy and Silicon-Germanium (SiGe) Deposition Solutions',
        'url': 'https://www.appliedmaterials.com/us/en/semiconductor/products/epitaxy.html'
    },
    {
        'id': 'amat_metrology_inspection',
        'title': 'Process Control, E-beam Inspection and Metrology',
        'url': 'https://www.appliedmaterials.com/us/en/semiconductor/products/pattern-suppression-verification.html'
    },
    {
        'id': 'amat_hybrid_bonding',
        'title': 'Hybrid Bonding and Heterogeneous Integration Packaging',
        'url': 'https://www.appliedmaterials.com/us/en/semiconductor/advanced-packaging/hybrid-bonding.html'
    }
]

def clean_html(raw_html):
    body = re.sub(r'<script[^>]*>.*?</script>', '', raw_html, flags=re.DOTALL)
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
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

print("Downloading AMAT solution pages...")
for item in amat_targets:
    file_path = os.path.join(amat_dir, f"{item['id']}.md")
    print(f"Downloading: {item['title']}...")
    try:
        req = urllib.request.Request(item['url'], headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            raw_html = resp.read().decode('utf-8', errors='ignore')
        md = clean_html(raw_html)
        header = f"""---
title: "{item['title']}"
source_url: "{item['url']}"
publisher: "Applied Materials (AMAT)"
source_id: "{item['id']}"
type: "official_equipment_solution"
---

# {item['title']}

"""
        full_content = header + md
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        print(f"  -> Saved {len(full_content):,} chars to {os.path.basename(file_path)}")
    except Exception as e:
        print(f"  -> Error: {e}")

print("AMAT download finished!")
