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

out_dir = r'c:\Users\BISTelligence\ontology-wiki\sources\lam_research'
os.makedirs(out_dir, exist_ok=True)

# 1. Fetch Technical Glossary
url_glossary = 'https://www.lamresearch.com/technical-glossary/'
print("Downloading Lam Research Technical Glossary...")
req = urllib.request.Request(url_glossary, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    html_raw = resp.read().decode('utf-8', errors='ignore')

# Regex to extract term name and definition container
pattern = r'<h4[^>]*>.*?<a[^>]*name=[\"\']([^\"\']+)[\"\'][^>]*>.*?</a>\s*(.*?)\s*</h4>\s*<div class=[\"\']glossary-description-container[\"\']>\s*(.*?)\s*</div>'
matches = re.findall(pattern, html_raw, re.DOTALL)
print(f"Extracted {len(matches)} official Lam Research glossary terms!")

glossary_entries = []
for slug, term, definition in matches:
    clean_term = re.sub(r'<[^>]+>', '', term).strip()
    clean_def = re.sub(r'<[^>]+>', '', definition).strip()
    clean_def = re.sub(r'\s+', ' ', clean_def)
    clean_def = html.unescape(clean_def)
    clean_term = html.unescape(clean_term)
    if clean_term and clean_def:
        glossary_entries.append({'slug': slug, 'term': clean_term, 'definition': clean_def})

print(f"Valid glossary entries: {len(glossary_entries)}")
for e in glossary_entries[:15]:
    print(f" - [{e['term']}]: {e['definition'][:70]}...")

# Save to markdown
header = """---
title: "Lam Research Official Technical Glossary"
source_url: "https://www.lamresearch.com/technical-glossary/"
publisher: "Lam Research"
type: "official_equipment_glossary"
total_terms: {}
---

# Lam Research Official Technical Glossary

The following technical terms and definitions are provided by Lam Research, the global leader in semiconductor etch, deposition, and wafer fabrication equipment.

""".format(len(glossary_entries))

lines = []
for e in glossary_entries:
    lines.append(f"### {e['term']}\n- **Definition**: {e['definition']}\n- **Anchor**: `#{e['slug']}`\n")

full_md = header + '\n'.join(lines)
glossary_file = os.path.join(out_dir, "lam_technical_glossary.md")
with open(glossary_file, 'w', encoding='utf-8') as f:
    f.write(full_md)

print(f"Saved {len(full_md):,} characters to {glossary_file}")
