import urllib.request
import ssl
import sys

sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

redirect_urls = [
    'https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEG2wnAaSz9uBi1x5btNdvdoJXDGvXf228R0nnQyehxhWH5BGEC9fLUaH_-Li8194ArNTIgCF88lyHIJKF6cUwG0dxcuVsxMKxvxknVj9A09PElkZeImqaUtTOlfDh5QP8KD4oD7zsdy9Jnn1ZAK5xsJoT8iQaI2goWUSH1DQhJUvMD',
    'https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEVPBflQiKRsaoh2FG_tmw3qhHEnKBQYPLElEO-g9VnMewPx4UvjKoa4d1IieRmj2W-7R8ZAS6GrtUNeIqlRpw3zU2x9GWhjqJodHW_q7E7Lq9YP9MNMMFC5kkJjOh6UzbRTlhjVdnjssSJuh_Td9ki-eExNFbXdtkN73xUpharcACewaoEnw=='
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for u in redirect_urls:
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
            print(f"Redirect target: {resp.geturl()} -> Status: {resp.status}, Size: {len(resp.read())}")
    except Exception as e:
        print(f"Error {u[:50]}: {e}")
