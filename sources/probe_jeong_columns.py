import urllib.request
import urllib.parse
import re
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

candidates = [
    'jeonginseong-column-intro',
    'jeonginseong-column-oxidation',
    'jeonginseong-column-photo',
    'jeonginseong-column-etch',
    'jeonginseong-column-etching',
    'jeonginseong-column-thinfilm',
    'jeonginseong-column-deposition',
    'jeonginseong-column-interconnect',
    'jeonginseong-column-metal',
    'jeonginseong-column-frontend-1',
    'jeonginseong-column-frontend-2',
    'jeonginseong-column-frontend-3',
    'jeonginseong-column-frontend-4',
    'jeonginseong-column-frontend-5',
    'jeonginseong-column-frontend-6',
    'jeonginseong-column-1',
    'jeonginseong-column-2',
    'jeonginseong-column-3',
    'jeonginseong-column-4',
    'jeonginseong-column-5',
    'jeonginseong-column-6'
]

print("Probing Jeong In-seong Front-end column URLs...")
for c in candidates:
    url = f"https://news.skhynix.co.kr/{c}/"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            if resp.status == 200:
                html = resp.read().decode('utf-8', errors='ignore')
                title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL)
                title = title_match.group(1).split('|')[0].strip() if title_match else c
                print(f" [FOUND 200] {title} -> {url}")
    except Exception:
        pass
