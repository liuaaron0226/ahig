# -*- coding: utf-8 -*-
"""第九型自查之第二階段：**由程式行為分流，不由我逐一宣稱**。

⚠️ 第一階段（n75_type9_audit.py）留下 114 個未分類，若我逐一手寫分類，
那份分類本身又會是「我的敘述」——**同一個陷阱換一層。**

故本檔改為由**程式碼特徵**分流：

  A. **只寫不讀**：檔內出現 `V['` 判讀建置樣式且未讀取既有 reason
     → 判讀建置檔（`mk_p*.py`），**不構成第九型**（它產生敘述，不消費）。
  B. **讀 reason 但同時讀 title/abstract**：有替代資料來源可交叉
     → 需人工檢視，惟風險較低。
  C. **只讀 reason，未讀 title/abstract**：**第九型之高風險樣式**
     → 逐一列出，需人工判定其檢查對象。

🚨 本檔輸出的是**風險分層**，不是判定。C 級仍須逐檔看它問的是什麼問題。
"""
import glob
import io
import re

READ_REASON = re.compile(r"\['reason'\]|e\.get\('reason'\)|"
                         r"\breason\b\s*=\s*e\[")
READ_TITLE = re.compile(r"\['title'\]|get\('title'\)|"
                        r"\['abstract'\]|get\('abstract'\)")
BUILDER = re.compile(r"^V\['[0-9a-f]{8}'\]\s*=", re.M)

a, b, c = [], [], []
for p in sorted(glob.glob('.scratch/*.py')):
    try:
        src = io.open(p, encoding='utf-8').read()
    except Exception:
        continue
    name = p.replace('\\', '/').split('/')[-1]
    if "'reason'" not in src and 'reason' not in src:
        continue
    reads = bool(READ_REASON.search(src))
    if BUILDER.search(src) and not reads:
        a.append(name)
    elif not reads:
        continue
    elif READ_TITLE.search(src):
        b.append(name)
    else:
        c.append(name)

print('== A：判讀建置檔（產生敘述，不消費）——不構成第九型 ==')
print('   %d 個：%s%s' % (len(a), '、'.join(a[:6]),
                          '…等' if len(a) > 6 else ''))
print()
print('== B：讀 reason 且同時讀 title/abstract（有替代來源可交叉）==')
print('   %d 個' % len(b))
for n in b:
    print('      ' + n)
print()
print('== 🚨 C：只讀 reason、未讀 title/abstract（第九型高風險樣式）==')
print('   %d 個' % len(c))
for n in c:
    print('      ' + n)
print()
print('⚠️ C 級不等於第九型——若其檢查對象**本來就是我的敘述**')
print('   （族序號、夾雜外文、引述正確性），那是正當的。')
print('🚨 C 級之判定仍須逐檔看它問的是什麼問題，本檔只做風險分層。')
