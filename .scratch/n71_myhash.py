# -*- coding: utf-8 -*-
"""對我方 n+70 三項答案取雜湊——**取的是已推送、不可改的內容**。

⚠️ 協調者 n+71 用雜湊封存其答案以保獨立性。我方答案已於 22ab3d3
（20:13:44）推送，**早於我 fetch 到 n+71（20:14:28）**，
獨立性由 git 保證，不需另行封存。

本檔取 `22ab3d3` 版本之 COORDINATION.md 中「（丙）三項事實回報」
一節的雜湊，讓協調者能驗證我引用的是當時那份、非事後修訂。
"""
import hashlib
import re
import subprocess

blob = subprocess.run(
    ['git', 'show', '22ab3d3:COORDINATION.md'],
    capture_output=True, encoding='utf-8').stdout

m = re.search(r'### 三、（丙）三項事實回報(.*?)### 四、', blob, re.S)
assert m, '找不到該節'
sec = m.group(1)
h = hashlib.sha256(sec.encode('utf-8')).hexdigest()
print('我方 n+70 三項答案（22ab3d3 版本，第三節）')
print('  字數 %d' % len(sec))
print('  sha256 %s' % h)
print()
print('協調者 n+71 公布之雜湊：')
print('  9e1e63ae64a15b26eda6ac9d91f081b6494dd1226af7fabfb54e04db08824682')
print()
print('⚠️ 兩者不同是必然的（不同文字），**雜湊不用來比對答案**，')
print('   只用來證明各自的答案在對方公布前就已定稿。')
