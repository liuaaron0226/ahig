"""Sort BixLink product photos into numbered Chinese-named folders by EXIF caption.

Copies (never moves). Originals stay flat in the source folder.
Run with --apply to actually copy; default is a dry run.
"""
import os, sys, json, shutil, io, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC = r'F:\德國參展\產品照片'
AUDIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photo-audit.json')
APPLY = '--apply' in sys.argv

# canonical caption -> folder name (chapter order for the Munich site)
FOLDERS = [
    ('24V/48V鋰離子電池組',        '01_24V-48V鋰離子電池組'),
    ('24V鋰鐵電池組',              '02_24V鋰鐵電池組'),
    ('4S2P 18650鋰電池組',         '03_4S2P-18650鋰電池組'),
    ('4S1P 18650鋰電池組',         '04_4S1P-18650鋰電池組'),
    ('3S2P 18650鋰電池組',         '05_3S2P-18650鋰電池組'),
    ('3S1P 18650鋰電池組',         '06_3S1P-18650鋰電池組'),
    ('2S1P 18650鋰電池組',         '07_2S1P-18650鋰電池組'),
    ('1S1P hard pack鋰電池組',     '08_1S1P-hard-pack鋰電池組'),
    ('1S1P 553450鋰電池組',        '09_1S1P-553450鋰電池組'),
    ('4S1P軟包鋰電池組',           '10_4S1P軟包鋰電池組'),
    ('1S2P軟包鋰電池組',           '11_1S2P軟包鋰電池組'),
    ('1S軟包鋰電池組',             '12_1S軟包鋰電池組'),
    ('軟包電池組系列',             '13_軟包電池組系列'),
    ('可充式鈕扣型電池',           '14_可充式鈕扣型電池'),
    ('可充式pin type鈕扣型電池',   '15_可充式pin-type鈕扣型電池'),
    ('CR一次性電池',               '16_CR一次性電池'),
    ('CR pin type coin battery',   '17_CR-pin-type鈕扣型電池'),
    ('Wire harness type CR coin battery', '18_CR-wire-harness鈕扣型電池'),
]
FOLDER_OF = dict(FOLDERS)

# raw EXIF caption -> canonical caption. Typing variants only (spacing, case,
# full/half-width parens, word order); genuinely different variants stay apart.
CANON = {
    '24V/48V鋰離子電池組': '24V/48V鋰離子電池組',
    '24V /48V鋰離子電池組': '24V/48V鋰離子電池組',
    '24V鋰鐵電池組': '24V鋰鐵電池組',
    '24V 鋰鐵電池組': '24V鋰鐵電池組',
    '4S2P 18650鋰電池組': '4S2P 18650鋰電池組',
    '4S1P 18650鋰電池組': '4S1P 18650鋰電池組',
    '3S2P 18650 鋰電池組': '3S2P 18650鋰電池組',
    '3S1P 18650鋰電池組': '3S1P 18650鋰電池組',
    '2S1P 18650 鋰電池組': '2S1P 18650鋰電池組',
    '1S1P hard pack鋰電池組': '1S1P hard pack鋰電池組',
    '1S1P 553450鋰電池組': '1S1P 553450鋰電池組',
    '4S 1P軟包鋰電池組': '4S1P軟包鋰電池組',
    '1S2P軟包鋰電池組': '1S2P軟包鋰電池組',
    '1S軟包鋰電池組': '1S軟包鋰電池組',
    '1s軟包鋰電池組': '1S軟包鋰電池組',
    '1S軟包鋰電池組(背面）': '1S軟包鋰電池組',
    '1S軟包鋰電池組（背面）': '1S軟包鋰電池組',
    '軟包電池組系列': '軟包電池組系列',
    '可充式鈕扣型電池': '可充式鈕扣型電池',
    '可充式pin type 鈕扣型電池': '可充式pin type鈕扣型電池',
    'CR一次性電池': 'CR一次性電池',
    'CR pin type coin battery': 'CR pin type coin battery',
    'Pin type CR coin battery': 'CR pin type coin battery',
    'Wire harness type CR coin battery': 'Wire harness type CR coin battery',
}

rows = json.load(open(AUDIT, encoding='utf-8'))

# The audit read JPGs where available; on disk every file is HEIC.
plan = collections.OrderedDict((f, []) for _, f in FOLDERS)
unknown = []
missing = []

for r in rows:
    base = os.path.splitext(r['file'])[0]
    canon = CANON.get(r['desc'])
    if canon is None:
        unknown.append((r['file'], r['desc']))
        continue
    # Most files are HEIC, but a couple landed as JPG.
    src = None
    for ext in ('.HEIC', '.heic', '.JPG', '.jpg'):
        p = os.path.join(SRC, base + ext)
        if os.path.exists(p):
            src = p
            break
    if src is None:
        missing.append(r['file'])
        continue
    plan[FOLDER_OF[canon]].append(src)

print('mode:', 'APPLY' if APPLY else 'DRY RUN')
print()
total = 0
for folder, files in plan.items():
    print('[%3d] %s' % (len(files), folder))
    total += len(files)
    if not APPLY:
        continue
    dest = os.path.join(SRC, folder)
    os.makedirs(dest, exist_ok=True)
    for src in files:
        shutil.copy2(src, os.path.join(dest, os.path.basename(src)))

print()
print('planned:', total, 'of', len(rows))
if unknown:
    print('UNMAPPED CAPTIONS:')
    for f, d in unknown:
        print('  %s  %r' % (f, d))
if missing:
    print('MISSING ON DISK:', missing)
