import urllib.request
import re
import json
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://semiconductor.samsung.com/kr/support/tools-resources/fabrication-process/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
    html = resp.read().decode('utf-8', errors='ignore')

scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for i in [5, 21]:
    if i < len(scripts):
        print(f'=== SCRIPT {i} ===')
        print(scripts[i][:1500])
