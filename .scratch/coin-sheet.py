"""Zoom sheet for the coin-cell folders so CR primary vs LIR rechargeable can be told apart."""
import os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from PIL import Image, ImageDraw
import pillow_heif
pillow_heif.register_heif_opener()

SRC = r'F:\德國參展\產品照片'
OUT = os.path.dirname(os.path.abspath(__file__))
TARGETS = ['14_可充式鈕扣型電池', '15_可充式pin-type鈕扣型電池',
           '16_CR一次性電池', '17_CR-pin-type鈕扣型電池',
           '18_CR-wire-harness鈕扣型電池']

CELL = 700
COLS = 3

items = []
for folder in TARGETS:
    p = os.path.join(SRC, folder)
    files = sorted(f for f in os.listdir(p) if not f.startswith('._'))
    for f in files:
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
canvas.save(os.path.join(OUT, 'sheet-coin.jpg'), quality=90)
print('wrote sheet-coin.jpg', len(items), 'cells')
