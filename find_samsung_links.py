import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\BISTelligence\.gemini\antigravity\brain\3373c5bb-c7fa-4a81-8de7-824b0f485e32\.system_generated\steps\155\content.md', 'r', encoding='utf-8') as f:
    text = f.read()

# find any eight-essential or part- or wafer or oxidation
matches = re.findall(r'([a-zA-Z0-9_\-\/]*eight-essential[a-zA-Z0-9_\-\/]*)', text)
print(f"Matches for 'eight-essential': {len(set(matches))}")
for m in sorted(list(set(matches)))[:20]:
    print(" -", m)

# search for part-1, part-2 etc
parts = re.findall(r'([a-zA-Z0-9_\-\/]*part-[1-8][a-zA-Z0-9_\-\/]*)', text)
print(f"Matches for 'part-X': {len(set(parts))}")
for p in sorted(list(set(parts)))[:20]:
    print(" -", p)
