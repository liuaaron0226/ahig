import json, io, sys, collections, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

here = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(here, 'photo-audit.json'), encoding='utf-8'))

g = collections.OrderedDict()
for r in rows:
    g.setdefault(r['desc'], []).append(r)

for k, v in g.items():
    dims = sorted(set('%dx%d' % (x['w'], x['h']) for x in v))
    px = [x['w'] * x['h'] for x in v]
    small = sum(1 for p in px if p < 3000000)
    flag = '   <-- %d small' % small if small else ''
    print('[%2d] %-34s %s%s' % (len(v), k, ', '.join(dims[:4]), flag))
