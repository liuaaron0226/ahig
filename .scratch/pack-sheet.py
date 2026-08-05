"""Zoom sheet for folders 01/02 (industrial enclosures) plus the pouch group folders."""
import os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from PIL import Image, ImageDraw
import pillow_heif
pillow_heif.register_heif_opener()

SRC = r'F:\德國參展\產品照片'
OUT = os.path.dirname(os.path.abspath(__file__))
TARGETS = ['01_24V-48V鋰離子電池組', '02_24V鋰鐵電池組', '13_軟包電池組系列']

CELL = 620
COLS = 4
PICK = 8  # evenly spaced samples per folder

items = []
for folder in TARGETS:
    p = os.path.join(SRC, folder)
    files = sorted(f for f in os.listdir(p) if not f.startswith('._'))
    step = max(1, len(files) // PICK)
    for f in files[::step][:PICK]:
        items.append(('%s / %s' % (folder.split('_')[0], os.path.splitext(f)[0]),
                      os.path.join(p, f)))

rows = (len(items) + COLS - 1) // COLS
canvas = Image.new('RGB', (COLS * CELL, rows * (CELL + 26)), 'white')
d = ImageDraw.Draw(canvas)
for i, (label, path) in enumerate(items):
    x = (i % COLS) * CELL
    y = (i // COLS) * (CELL + 26)
    im = Image.open(path)
    im.thumbnail((CELL - 8, CELL - 8))
    canvas.paste(im, (x + 4, y + 4))
    d.text((x + 6, y + CELL + 6), label, fill='black')
canvas.save(os.path.join(OUT, 'sheet-pack.jpg'), quality=90)
print('wrote sheet-pack.jpg', len(items), 'cells')
