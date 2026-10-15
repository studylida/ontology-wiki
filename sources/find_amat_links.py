import urllib.request
import re
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://www.appliedmaterials.com/'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        print(f"Main page Status: {resp.status}, Size: {len(html)}")
        
        # search for products links
        links = re.findall(r'href=[\"\'](/[^\"\']*(?:product|cmp|epitaxy|inspection)[^\"\']*)[\"\']', html, re.I)
        print(f"Found {len(links)} product links:")
        for l in set(links)[:25]:
            print(" -", l)
except Exception as e:
    print(f"Error {url}: {e}")
