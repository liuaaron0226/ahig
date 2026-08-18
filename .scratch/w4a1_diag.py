"""診斷 W4a-1 之 incomplete 216 筆究竟卡在哪一步。

不從程式碼推論，直接讀落盤的 manifest attempts。
只輸出彙總計數與 candidateId，不含任何文獻內容。
"""
import hashlib, json, os, re
from collections import Counter

ROOT = r'C:/Users/User/Desktop/claude/ahig-private/fulltext'
status = json.load(open('.scratch/w4a1_status.json', encoding='utf-8'))

def artifact_dir(cid):
    # 與 fulltext._candidate_directory_name 相同的命名，逐字照抄不重打
    digest = hashlib.sha256(cid.encode('utf-8')).hexdigest()[:16]
    human = cid.rsplit(':', 1)[-1]
    slug = re.sub(r'[^A-Za-z0-9._-]+', '-', human).strip('-.').lower()
    slug = (slug[:32].rstrip('-.') or 'candidate')
    return os.path.join(ROOT, '%s-%s' % (slug, digest))

combo = Counter()
per_source = {'europe-pmc': Counter(), 'openalex': Counter(), 'unpaywall': Counter()}
for cid in status.get('incomplete', []):
    p = os.path.join(artifact_dir(cid), 'manifest.json')
    m = json.load(open(p, encoding='utf-8'))
    key = []
    for a in m.get('attempts', []):
        src, con = a.get('sourceId'), a.get('conclusion')
        key.append('%s=%s' % (src, con))
        if src in per_source:
            per_source[src][con] += 1
        if con not in ('miss', 'hit'):
            r = a.get('reason')
            if r:
                per_source.setdefault(src, Counter())['reason:' + r] += 1
    combo[' | '.join(key)] += 1

print('incomplete total', sum(combo.values()))
for k, v in combo.most_common():
    print('  %4d  %s' % (v, k))
print()
for src, c in per_source.items():
    print(src, dict(c.most_common()))
