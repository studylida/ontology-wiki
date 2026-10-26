"""Generate local development secrets without printing or overwriting them."""
from pathlib import Path
import secrets

path = Path('.env')
if path.exists():
    raise SystemExit('.env already exists; no changes made')
password, signing_secret = secrets.token_hex(24), secrets.token_hex(48)
text = Path('.env.example').read_text().replace('replace-with-random-url-safe-value', password).replace('replace-with-at-least-32-random-characters', signing_secret)
with path.open('x') as handle:
    handle.write(text)
path.chmod(0o600)
print('Created private development .env. No credentials were printed.')
