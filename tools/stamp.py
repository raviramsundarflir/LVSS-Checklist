#!/usr/bin/env python3
"""Keep every app's embedded build stamp in step with its version.json.

Each app page carries  var B='<build>'  and  var S='<suite>';window.__SUITE
and the app compares B with version.json to show "A new version is available".
If they differ the banner shows forever (this happened in Rev 94).

  python3 tools/stamp.py --check   exit 1 and list mismatches (used before every push and in CI)
  python3 tools/stamp.py           rewrite the page stamps to match version.json
"""
import glob, json, os, re, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fix = '--check' not in sys.argv
bad = 0
def rd(p): return open(p, encoding='utf-8').read()
suites = set()
for vj in sorted(glob.glob(os.path.join(root, '*', 'version.json'))):
    d = os.path.dirname(vj); name = os.path.basename(d); j = json.load(open(vj)); suites.add(j['suite'])
    page = os.path.join(d, 'index.html'); s = rd(page)
    sw = os.path.join(d, 'sw.js'); swt = rd(sw) if os.path.exists(sw) else ''
    mb = re.search(r"var B='([0-9a-f]+)'", s); ms = re.search(r"var S='([0-9a-f]+)';window\.__SUITE", s)
    probs = []
    if not mb: probs.append('no build stamp in page')
    elif mb.group(1) != j['build']: probs.append(f"page build {mb.group(1)} != version.json {j['build']}")
    if ms and ms.group(1) != j['suite']: probs.append(f"page suite {ms.group(1)} != version.json {j['suite']}")
    if swt and j['build'] not in swt: probs.append('sw.js cache name does not contain the version.json build')
    if probs:
        bad += 1; print(f'{name}: ' + '; '.join(probs))
        if fix and mb:
            s = re.sub(r"var B='[0-9a-f]+'", f"var B='{j['build']}'", s, count=1)
            s = re.sub(r"var S='[0-9a-f]+';window\.__SUITE", f"var S='{j['suite']}';window.__SUITE", s)
            open(page, 'w', encoding='utf-8').write(s); print('  -> page stamps rewritten')
if len(suites) > 1: bad += 1; print('version.json files disagree on the suite:', suites)
rp = os.path.join(root, 'index.html')
if suites and os.path.exists(rp):
    m = re.search(r"var S='([0-9a-f]+)';window\.__SUITE", rd(rp)); su = next(iter(suites))
    if m and m.group(1) != su:
        bad += 1; print(f'launcher suite {m.group(1)} != {su}')
        if fix: open(rp, 'w', encoding='utf-8').write(re.sub(r"var S='[0-9a-f]+';window\.__SUITE", f"var S='{su}';window.__SUITE", rd(rp))); print('  -> launcher stamp rewritten')
print('stamps OK' if not bad else ('mismatches found' + (' and fixed' if fix else '')))
sys.exit(1 if (bad and not fix) else 0)
