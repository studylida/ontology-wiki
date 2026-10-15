import urllib.request
import re
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url_kr = 'https://www.lamresearch.com/ko/technical-glossary/'
req = urllib.request.Request(url_kr, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
    html_kr = resp.read().decode('utf-8', errors='ignore')

# look for "glossary-item" or similar
items = re.findall(r'<div[^>]*class=[\"\'][^\"\']*glossary[^\"\']*[\"\'][^>]*>(.*?)</div>', html_kr, re.DOTALL)
print(f"Glossary div items: {len(items)}")

# search for "3D NAND" or "ALD" in html
idx = html_kr.find('3D NAND')
if idx != -1:
    print("Found '3D NAND' in html:")
    print(html_kr[max(0, idx-150):min(len(html_kr), idx+400)])
