import os, glob, json, sys, collections, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

JPG = r'D:\UserData\Downloads\新增資料夾 (2)'
HEIC = r'F:\德國參展\產品照片'

jpgs = sorted(glob.glob(os.path.join(JPG, '*.*')))
heics = [f for f in sorted(os.listdir(HEIC)) if not f.startswith('._')]

print('JPG files:', len(jpgs))
print('HEIC files:', len(heics))

from PIL import Image
from PIL.ExifTags import TAGS

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_OK = True
except ImportError:
    HEIF_OK = False
print('pillow_heif available:', HEIF_OK)
print()


def read(path):
    desc = ''
    w = h = 0
    try:
        im = Image.open(path)
        w, h = im.size
        ex = im.getexif()
        for tag, val in ex.items():
            if TAGS.get(tag) == 'ImageDescription':
                if isinstance(val, bytes):
                    desc = val.decode('utf-8', 'ignore')
                else:
                    # Pillow decodes EXIF ASCII as latin-1; real bytes are UTF-8
                    try:
                        desc = val.encode('latin-1').decode('utf-8')
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        desc = val
    except Exception as e:
        desc = 'ERROR: %s' % e
    return desc.strip(), w, h


rows = []
for f in jpgs:
    d, w, h = read(f)
    rows.append({'file': os.path.basename(f), 'src': 'jpg', 'desc': d, 'w': w, 'h': h})

if HEIF_OK:
    have = set(os.path.splitext(r['file'])[0] for r in rows)
    for f in heics:
        base = os.path.splitext(f)[0]
        if base in have:
            continue
        d, w, h = read(os.path.join(HEIC, f))
        rows.append({'file': f, 'src': 'heic', 'desc': d, 'w': w, 'h': h})

rows.sort(key=lambda r: r['file'])

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photo-audit.json')
with open(out, 'w', encoding='utf-8') as fh:
    json.dump(rows, fh, ensure_ascii=False, indent=1)

groups = collections.OrderedDict()
for r in rows:
    groups.setdefault(r['desc'] or '(NO CAPTION)', []).append(r)

print('=== %d CAPTION GROUPS / %d files ===' % (len(groups), len(rows)))
for k, v in groups.items():
    files = [x['file'] for x in v]
    dims = sorted(set('%dx%d' % (x['w'], x['h']) for x in v))
    srcs = sorted(set(x['src'] for x in v))
    print('[%3d] %s' % (len(v), k))
    print('      %s ... %s  (%s)' % (files[0], files[-1], '/'.join(srcs)))
    print('      dims: %s' % ', '.join(dims))
print()
print('written:', out)
