# -*- coding: utf-8 -*-
"""n+59 第四節之常規化檢查：**任何呈現為結論的字串，必須由當次資料
現算；不得硬寫。**

本檔對 `.scratch/` 內所有 `.py` 做內容制掃描，找出「印出結論語彙、
而該行不含任何變數插值」之字面量——即硬寫結論之候選。

判準（機械式，不含人工挑選）：
  1. 該行為 print(...) 或字串常數，且
  2. 含結論語彙（通過／未過／成立／不成立／PASS／FAIL／顯著／
     重疊／p = 數字／倍 等），且
  3. **不含任何格式化插值**（無 %、無 .format、無 f-string、
     無 str(）、無 + 變數）——即該結論不可能隨資料改變。

⚠️ 命中不等於缺陷：說明性文字（判準敘述、提醒、欄位標題）
也可能命中。故本檔**只列出候選並標明所在行**，由人逐筆判讀，
不自行宣告「零缺陷」。本檔自身之結語亦由掃描結果現算。
"""
import io
import os
import re

ROOT = '.scratch'

VERDICT = re.compile(
    r'通過|未過|不成立|成立|PASS|FAIL|顯著|重疊|不重疊|'
    r'p\s*=\s*0\.\d+|\d+\.\d+\s*倍|門檻')

# 插值跡象：任一存在即代表該行可隨資料改變
INTERP = re.compile(r'%[sdfr\d\.]|%\s*\(|\.format\(|f\'|f"|str\(|\{\}|\{\d|\{[a-z_]+\}')


def scan(path):
    hits = []
    try:
        lines = io.open(path, encoding='utf-8').read().split('\n')
    except (UnicodeDecodeError, OSError):
        return hits
    for n, line in enumerate(lines, 1):
        if not VERDICT.search(line):
            continue
        if INTERP.search(line):
            continue          # 會隨資料改變，不是硬寫結論
        if not re.search(r'''['"]''', line):
            continue          # 非字串，多半是變數名或註解符號外的程式
        hits.append((n, line.strip()))
    return hits


files = []
for dirpath, _dirnames, filenames in os.walk(ROOT):
    for fn in sorted(filenames):
        if fn.endswith('.py'):
            files.append(os.path.join(dirpath, fn))

total_hits = 0
files_with_hits = 0
print('=== n+59 第四節：硬寫結論候選掃描 ===')
print('掃描 %d 個 .py 檔' % len(files))
print()
for f in files:
    hits = scan(f)
    if not hits:
        continue
    files_with_hits += 1
    total_hits += len(hits)
    print('--- %s（%d 處）' % (f.replace('\\', '/'), len(hits)))
    for n, line in hits:
        print('  L%-5d %s' % (n, line[:150]))
    print()

print('=' * 60)
print('候選 %d 處，分布於 %d 個檔案（掃描 %d 檔）'
      % (total_hits, files_with_hits, len(files)))
print('⚠️ 候選不等於缺陷——需逐筆判讀該字串是否「呈現為結論」。')
print('   說明性文字（判準敘述、欄位標題、提醒）命中屬預期。')
