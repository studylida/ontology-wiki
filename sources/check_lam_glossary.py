import urllib.request
import re
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    'https://www.lamresearch.com/technical-glossary/',
    'https://www.lamresearch.com/ko/technical-glossary/',
    'https://www.lamresearch.com/technology-solutions/etch/',
    'https://www.lamresearch.com/technology-solutions/deposition/',
    'https://www.lamresearch.com/technology-solutions/clean/',
    'https://www.lamresearch.com/ko/technology-solutions/',
    'https://newsroom.lamresearch.com/'
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            print(f"URL: {u} -> Status: {resp.status}, Size: {len(resp.read())}")
    except Exception as e:
        print(f"Error {u}: {e}")
