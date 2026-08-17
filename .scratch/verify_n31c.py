# -*- coding: utf-8 -*-
import json, re
OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs/'
       r'b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1')
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
rc = json.load(open(OUT + '/post-ruling-reclassification.json', encoding='utf-8'))
ov = {e['candidateId']: e for e in rc['entries']}
item = {it['candidateId']: it for it in w['items']}
pat = re.compile(r'recreationally[- ]trained', re.I)

# non-population axis keywords that would independently justify exclusion
other_axis = re.compile(
    r'漱口|咖啡因|prednisolone|糖皮質素|醋酸|益生菌|CYP1A2|蜂蜜|salbutamol|'
    r'timing 軸不符|運動前|恢復期|阻力運動|mixed-nutrient|裁定 59/60|裁定 78|'
    r'介入軸不符|運動型態|outcome-adjacent|裁定 n\+27')

print('%-10s %-8s %s' % ('id', 'eff', 'independent-other-axis?'))
for e in d['entries']:
    cid = e['candidateId']
    o = ov.get(cid)
    eff = o['effectiveDecision'] if o else e['opinion']
    if eff == 'unclear':
        continue
    ab = (item.get(cid, {}).get('abstract') or '')
    ti = (item.get(cid, {}).get('title') or '')
    if not (pat.search(ab) or pat.search(ti) or pat.search(e['reason'])):
        continue
    txt = e['reason'] + ' ' + ((o.get('note') or '') if o else '')
    ok = bool(other_axis.search(txt))
    print('%-10s %-8s %s' % (cid[-8:], eff, 'YES' if ok else '*** NO — REVIEW ***'))
    if not ok:
        print('     reason:', e['reason'][:260])
