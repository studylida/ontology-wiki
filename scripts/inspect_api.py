import sys
import json
from backend.app.main import app

schema = app.openapi()
paths = schema.get('paths', {})
catalog = {}

for p, methods_data in sorted(paths.items()):
    for method, info in methods_data.items():
        if method.lower() in ('head', 'options'):
            continue
        tag = (info.get('tags') or ['Uncategorized'])[0]
        catalog.setdefault(tag, []).append({
            'method': method.upper(),
            'path': p,
            'summary': info.get('summary', ''),
            'operationId': info.get('operationId', '')
        })

print(f"=== TOTAL ENDPOINTS: {sum(len(v) for v in catalog.values())} across {len(catalog)} TAGS ===\n")
for tag, eps in sorted(catalog.items()):
    print(f"## [{tag}] ({len(eps)} endpoints)")
    for ep in eps:
        print(f"  - {ep['method']:6} {ep['path']:55} | {ep['summary']}")
