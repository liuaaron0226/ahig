import json, io, sys, collections, os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

here = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(here, 'photo-audit.json'), encoding='utf-8'))

FULL = {(3024, 4032), (4032, 3024), (6048, 8064), (8064, 6048)}

g = collections.OrderedDict()
for r in rows:
    g.setdefault(r['desc'], []).append(r)

for k, v in g.items():
    cropped = [x for x in v if (x['w'], x['h']) not in FULL]
    if not cropped:
        continue
    print('%s  -- %d/%d cropped' % (k, len(cropped), len(v)))
    for x in cropped:
        print('    %-16s %dx%d' % (x['file'], x['w'], x['h']))
