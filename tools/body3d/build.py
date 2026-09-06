#!/usr/bin/env python3
"""把 human-atlas 轉檔後的 BodyParts3D 4.0 選出肌肉／骨頭／皮膚，簡化、量化、打包。

來源：https://github.com/ashemag/human-atlas （public/models/atlas.json + body-*.bin）
      其人體資料為 BodyParts3D 4.0，© The Database Center for Life Science，CC BY 4.0
      （依 human-atlas 之 public/ATTRIBUTION.md 所述；本室無法直接連到原站核對）。
輸出：tools/body3d/atlas.json（清單，含中文名、關節座標）
      tools/body3d/atlas.bin （Int16 座標 + Uint16 索引）
      tools/body-3d.html     （template.html 塞入 base64 之後的成品）

用法：python3 tools/body3d/build.py [HUMAN_ATLAS_MODELS_DIR]
"""
import base64, json, re, struct, sys
from pathlib import Path
import numpy as np
import fast_simplification

HERE = Path(__file__).resolve().parent
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else '/home/user/ashemag/human-atlas/public/models')

# ── 1. 選哪些部位 ──────────────────────────────────────────────
# 🚫 排除：心臟乳頭肌、眼外肌、喉／咽／舌／顎、骨盆底、舌骨肌群、深層頸椎小肌、
#          手足內在小肌、內層肋間肌、橫膈、牙齒、喉軟骨、顱底內部骨。
DROP = re.compile(r'''
  papillary|ventricle|
  ^(Left|Right)\ (inferior|superior)\ (oblique|rectus)$|^(Left|Right)\ (lateral|medial)\ rectus$|
  levator\ palpebrae|arytenoid|cricothyroid|vocalis|aryepiglotticus|genioglossus|hyoglossus|
  veli\ palatini|uvular|anal\ sphincter|coccygeus|puborectalis|perineal|levator\ ani|
  digastric|mylohyoid|geniohyoid|stylohyoid|omohyoid|sternohyoid|sternothyroid|thyrohyoid|
  longus\ colli|longus\ capitis|rectus\ capitis|obliquus\ capitis|intertransvers|interspinal|
  rotator$|levatores\ costarum|internal\ intercostal|innermost\ intercostal|transversus\ thoracis|
  ^Diaphragm$|lumbrical|interosse|opponens|abductor\ digiti|flexor\ digiti\ minimi|
  adductor\ hallucis|adductor\ pollicis|flexor\ hallucis\ brevis|abductor\ hallucis|
  abductor\ pollicis\ brevis|flexor\ pollicis\ brevis|flexor\ accessorius|extensor\ hallucis\ brevis|
  tooth|gingiva|cartilage$|^Hyoid|^Ethmoid|^Vomer|palatine\ bone|^Sphenoid|sesamoid|
  ^Cricoid|^Thyroid\ cartilage|alar\ cartilage|
  ligament|membrane|raphe|conus|trochlea|tendon\ of|intermediate\ tendon|linea\ alba|
  ^Pubic
''', re.I | re.X)
SKIN_PARTS = {'Skin', 'Eyebrow', 'Lip', 'Hair of head'}     # 外觀層：皮膚加上讓臉不像假人的三樣

KEEP_CONNECTIVE = re.compile(r'calcaneal tendon|tensor fasciae latae', re.I)
MUSCLE_IN_SKELETAL = re.compile(r'fibularis|tibialis|levator scapulae|subscapularis|iliotibial', re.I)

def group_of(p):
    n, s = p['name'], p['system']
    if s == 'integumentary': return 's' if n in SKIN_PARTS else None
    if s == 'connective':    return 'm' if KEEP_CONNECTIVE.search(n) else None
    if s == 'skeletal':      return 'm' if MUSCLE_IN_SKELETAL.search(n) else 'b'
    if s == 'muscular':      return 'm'
    return None

# ── 2. 中文名 ──────────────────────────────────────────────────
TERM = {
 'pectoralis major':'胸大肌','pectoralis minor':'胸小肌','deltoid':'三角肌','trapezius':'斜方肌',
 'serratus anterior':'前鋸肌','serratus posterior inferior':'下後鋸肌','serratus posterior superior':'上後鋸肌',
 'subclavius':'鎖骨下肌','biceps brachii':'肱二頭肌','triceps brachii':'肱三頭肌','brachialis':'肱肌',
 'brachioradialis':'肱橈肌','coracobrachialis':'喙肱肌','anconeus':'肘肌','supraspinatus':'棘上肌',
 'infraspinatus muscle':'棘下肌','infraspinatus':'棘下肌','teres major':'大圓肌','teres minor':'小圓肌',
 'subscapularis':'肩胛下肌','rhomboid major':'大菱形肌','rhomboid minor':'小菱形肌','levator scapulae':'提肩胛肌',
 'external oblique':'腹外斜肌','external intercostal muscle':'外肋間肌','sternocleidomastoid':'胸鎖乳突肌',
 'scalenus anterior':'前斜角肌','scalenus medius':'中斜角肌','scalenus posterior':'後斜角肌','platysma':'頸闊肌',
 'splenius capitis':'頭夾肌','splenius cervicis':'頸夾肌','semispinalis capitis':'頭半棘肌',
 'semispinalis cervicis':'頸半棘肌','semispinalis thoracis':'胸半棘肌','longissimus capitis':'頭最長肌',
 'longissimus cervicis':'頸最長肌','longissimus thoracis':'胸最長肌','iliocostalis cervicis':'頸髂肋肌',
 'iliocostalis lumborum':'腰髂肋肌','iliocostalis thoracis':'胸髂肋肌','spinalis thoracis':'胸棘肌','spinalis':'棘肌',
 'psoas major':'腰大肌','iliacus':'髂肌','gluteus maximus':'臀大肌','gluteus medius':'臀中肌','gluteus minimus':'臀小肌',
 'tensor fasciae latae':'闊筋膜張肌','iliotibial tract':'髂脛束','piriformis':'梨狀肌','obturator internus':'閉孔內肌',
 'obturator externus':'閉孔外肌','gemellus superior':'上孖肌','gemellus inferior':'下孖肌','quadratus femoris':'股方肌',
 'pectineus':'恥骨肌','adductor longus':'內收長肌','adductor brevis':'內收短肌','adductor magnus':'內收大肌',
 'adductor minimus':'內收小肌','gracilis':'股薄肌','sartorius':'縫匠肌','rectus femoris':'股直肌',
 'vastus lateralis':'股外側肌','vastus medialis':'股內側肌','vastus intermedius':'股中間肌','biceps femoris':'股二頭肌',
 'semitendinosus':'半腱肌','semimembranosus':'半膜肌','gastrocnemius':'腓腸肌','soleus':'比目魚肌','plantaris':'蹠肌',
 'popliteus':'膕肌','tibialis anterior':'脛前肌','tibialis posterior':'脛後肌','fibularis longus':'腓骨長肌',
 'fibularis brevis':'腓骨短肌','fibularis tertius':'第三腓骨肌','extensor digitorum longus':'伸趾長肌',
 'extensor hallucis longus':'伸拇長肌','flexor digitorum longus':'屈趾長肌','flexor hallucis longus':'屈拇長肌',
 'flexor digitorum brevis':'屈趾短肌',
 'calcaneal tendon':'跟腱（阿基里斯腱）','pronator teres':'旋前圓肌','flexor carpi radialis':'橈側屈腕肌',
 'palmaris longus':'掌長肌','flexor carpi ulnaris':'尺側屈腕肌','flexor digitorum superficialis':'屈指淺肌',
 'flexor digitorum profundus':'屈指深肌','flexor pollicis longus':'屈拇長肌','pronator quadratus':'旋前方肌',
 'extensor carpi radialis longus':'橈側伸腕長肌','extensor carpi radialis brevis':'橈側伸腕短肌',
 'extensor carpi ulnaris':'尺側伸腕肌','extensor digitorum':'伸指肌','extensor digiti minimi':'伸小指肌',
 'extensor indicis':'伸食指肌','extensor pollicis longus':'伸拇長肌','extensor pollicis brevis':'伸拇短肌',
 'abductor pollicis longus':'外展拇長肌','supinator':'旋後肌',
 # 骨
 'clavicle':'鎖骨','scapula':'肩胛骨','humerus':'肱骨','radius':'橈骨','ulna':'尺骨','scaphoid':'舟狀骨','lunate':'月骨',
 'triquetral':'三角骨','pisiform':'豆狀骨','trapezium':'大多角骨','trapezoid':'小多角骨','capitate':'頭狀骨','hamate':'鉤骨',
 'hip bone':'髖骨','femur':'股骨','patella':'髕骨','tibia':'脛骨','fibula':'腓骨','talus':'距骨','calcaneus':'跟骨',
 'cuboid bone':'骰骨','medial cuneiform bone':'內側楔狀骨','intermediate cuneiform bone':'中間楔狀骨',
 'lateral cuneiform bone':'外側楔狀骨','maxilla':'上頜骨','nasal bone':'鼻骨','parietal bone':'頂骨',
 'temporal bone':'顳骨','zygomatic bone':'顴骨',
 'thumb':'拇指','index finger':'食指','middle finger':'中指','ring finger':'無名指','little finger':'小指',
 'big toe':'拇趾','second toe':'第2趾','third toe':'第3趾','fourth toe':'第4趾','little toe':'小趾',
 'hand':'手','foot':'足',
}
PART = {'Clavicular part':'鎖骨部','Sternocostal part':'胸肋部','Abdominal part':'腹部','Acromial part':'肩峰部',
 'Spinal part':'肩胛棘部','Descending part':'上部','Transverse part':'中部','Ascending part':'下部',
 'Long head':'長頭','Short head':'短頭','Lateral head':'外側頭','Medial head':'內側頭','Humeral head':'肱骨頭',
 'Ulnar head':'尺骨頭','Proximal phalanx':'近節','Middle phalanx':'中節','Distal phalanx':'遠節','Navicular bone':'舟狀骨'}
ORD = {'first':1,'second':2,'third':3,'fourth':4,'fifth':5,'sixth':6,'seventh':7,'eighth':8,'ninth':9,'tenth':10,
       'eleventh':11,'twelfth':12}
WHOLE = {'Atlas':'寰椎（第1頸椎）','Axis':'樞椎（第2頸椎）','Body of sternum':'胸骨體','Manubrium':'胸骨柄',
 'Xiphoid process':'劍突','Sacrum':'薦骨','Mandible':'下頜骨','Frontal bone':'額骨','Occipital bone':'枕骨',
 'Skin':'皮膚','Eyebrow':'眉毛','Lip':'嘴唇','Hair of head':'頭髮','Intervertebral disk':'椎間盤','Spinal part of right deltoid':'右三角肌後束（肩胛棘部）',
 'Spinal part of left deltoid':'左三角肌後束（肩胛棘部）','Acromial part of right deltoid':'右三角肌中束（肩峰部）',
 'Acromial part of left deltoid':'左三角肌中束（肩峰部）','Clavicular part of right deltoid':'右三角肌前束（鎖骨部）',
 'Clavicular part of left deltoid':'左三角肌前束（鎖骨部）'}
SIDE = {'right':'右','left':'左'}
LEVEL = {'cervical':'頸椎','thoracic':'胸椎','lumbar':'腰椎'}

def zh(name):
    n = name.strip()
    if n in WHOLE: return WHOLE[n]
    m = re.match(r'^(\w+) (cervical|thoracic|lumbar) vertebra$', n, re.I)
    if m: return f'第{ORD[m[1].lower()]}{LEVEL[m[2].lower()]}'
    m = re.match(r'^Intervertebral disk of (\w+) (cervical|thoracic|lumbar) vertebra$', n, re.I)
    if m: return f'第{ORD[m[1].lower()]}{LEVEL[m[2].lower()]}椎間盤'
    if n == 'Intervertebral disk of axis': return '樞椎椎間盤'
    m = re.match(r'^(Right|Left) (\w+) (rib|costal cartilage|metacarpal bone|metatarsal bone)$', n, re.I)
    if m:
        k = {'rib':'肋骨','costal cartilage':'肋軟骨','metacarpal bone':'掌骨','metatarsal bone':'蹠骨'}[m[3].lower()]
        return f'{SIDE[m[1].lower()]}第{ORD[m[2].lower()]}{k}'
    m = re.match(r'^(Proximal|Middle|Distal) phalanx of (right|left) (.+)$', n, re.I)
    if m:
        digit = TERM.get(m[3].lower()); seg = PART[f'{m[1].capitalize()} phalanx']
        bone = '趾骨' if 'toe' in m[3].lower() else '指骨'
        if digit: return f'{SIDE[m[2].lower()]}{digit}{seg}{bone}'
    m = re.match(r'^(.+?) of (right|left) (.+)$', n, re.I)
    if m:
        part = PART.get(m[1]); base = TERM.get(m[3].lower())
        if part and base: return f'{SIDE[m[2].lower()]}{base}{part}'
        if m[1] == 'Navicular bone' and m[3].lower() == 'foot': return f'{SIDE[m[2].lower()]}足舟狀骨'
    m = re.match(r'^(Right|Left) (.+)$', n, re.I)
    if m:
        base = TERM.get(m[2].lower())
        if base: return f'{SIDE[m[1].lower()]}{base}'
    base = TERM.get(n.lower())
    if base: return base
    return None

# ── 3. 部位歸到哪一節骨頭（骨頭是剛體；肌肉與皮膚在網頁端用關節距離平滑分配）─
def side_of(name):
    n = name.lower()
    if re.search(r'\bright\b', n): return 'R'
    if re.search(r'\bleft\b', n):  return 'L'
    return ''

HAND_BONES = re.compile(r'scaphoid|lunate|triquetral|pisiform|trapezium|trapezoid|capitate|hamate|metacarpal|finger|thumb', re.I)
FOOT_BONES = re.compile(r'talus|calcaneus|cuboid|navicular|cuneiform bone|metatarsal|toe', re.I)
def bone_seg(name):
    if re.search(r'\brib\b|costal cartilage|sternum|manubrium|xiphoid', name, re.I): return 'chest'   # 呼吸時會撐開
    if re.search(r'humerus', name, re.I): return 'uarm'
    if re.search(r'radius|ulna', name, re.I): return 'farm'
    if HAND_BONES.search(name): return 'hand'
    if re.search(r'femur', name, re.I): return 'thigh'
    if re.search(r'patella|tibia|fibula', name, re.I): return 'shank'
    if FOOT_BONES.search(name): return 'foot'
    return 'torso'

# 給介面用的區域標籤
REGION = [
 ('chest', r'pectoralis|subclavius|serratus anterior|intercostal'),
 ('shoulder', r'deltoid|supraspinatus|infraspinatus|teres|subscapularis|coracobrachialis'),
 ('back', r'trapezius|rhomboid|levator scapulae|serratus posterior|splenius|semispinalis|longissimus|iliocostalis|spinalis'),
 ('arm', r'biceps brachii|triceps|brachialis|anconeus|brachioradialis'),
 ('forearm', r'pronator|flexor carpi|palmaris|flexor digitorum|flexor pollicis|extensor|abductor pollicis|supinator'),
 ('core', r'oblique|psoas|iliacus'),
 ('glute', r'gluteus|tensor fasciae|piriformis|obturator|gemellus|quadratus femoris'),
 ('thigh', r'pectineus|adductor|gracilis|sartorius|rectus femoris|vastus|biceps femoris|semitendinosus|semimembranosus|iliotibial'),
 ('calf', r'gastrocnemius|soleus|plantaris|popliteus|tibialis|fibularis|digitorum longus|hallucis longus|calcaneal'),
 ('neck', r'sternocleidomastoid|scalenus|platysma'),
]
def region_of(name, grp):
    if grp != 'm': return grp
    for k, pat in REGION:
        if re.search(pat, name, re.I): return k
    return 'other'

# ── 4. 讀取 ────────────────────────────────────────────────────
atlas = json.loads((SRC / 'atlas.json').read_text())
chunks = [ (SRC / c['url'].split('/')[-1]).read_bytes() for c in atlas['chunks'] ]

def geometry(p):
    b = chunks[p['chunk']]
    pos = np.frombuffer(b, dtype='<f4', count=p['vertexCount']*3, offset=p['positions']).reshape(-1,3).astype(np.float64)
    idx = np.frombuffer(b, dtype='<u4', count=p['indexCount'], offset=p['indices']).reshape(-1,3).astype(np.int64)
    return pos, idx

def raw(fj):
    return geometry(next(p for p in atlas['parts'] if p['id'] == fj))

# ── 5. 關節中心（由骨頭的頂端／底端算）────────────────────────
def end_centroid(pos, top, depth):
    y = pos[:,1]
    sel = pos[y >= y.max()-depth] if top else pos[y <= y.min()+depth]
    return sel.mean(axis=0)

def femoral_head(pos):
    # 股骨頂端 4 cm 內、最靠近中線那一叢（股骨頭在內側，大轉子在外側）
    top = pos[pos[:,1] >= pos[:,1].max()-0.04]
    medial = top[np.argmin(np.abs(top[:,0]))]
    return top[np.linalg.norm(top-medial, axis=1) < 0.025].mean(axis=0)

def by_name(sub):
    return raw(next(p for p in atlas['parts'] if p['name'].lower() == sub.lower())['id'])[0]

def joints_for(side):
    hum = raw('FJ3368' if side=='R' else 'FJ3262')[0]
    rad = raw('FJ3349' if side=='R' else 'FJ3277')[0]
    fem = raw('FJ3365' if side=='R' else 'FJ3259')[0]
    tib = raw('FJ3387' if side=='R' else 'FJ3282')[0]
    s = 'right' if side == 'R' else 'left'
    wrist = end_centroid(rad, False, 0.015)
    # 手掌的靜止朝向：由掌骨算，🚫 不假設資料是「掌心朝前」的解剖姿勢
    mc3 = by_name(f'{s} third metacarpal bone').mean(axis=0)
    mc1 = by_name(f'{s} first metacarpal bone').mean(axis=0)
    mc5 = by_name(f'{s} fifth metacarpal bone').mean(axis=0)
    hand_dir = mc3 - wrist; hand_dir /= np.linalg.norm(hand_dir)
    radial = mc1 - mc5; radial -= hand_dir * radial.dot(hand_dir); radial /= np.linalg.norm(radial)
    palm = np.cross(radial, hand_dir) if side == 'R' else np.cross(hand_dir, radial)   # 掌心＝拇指那側轉向手指方向
    return {
        'shoulder': end_centroid(hum, True, 0.035).tolist(),
        'elbow':    end_centroid(hum, False, 0.02).tolist(),
        'wrist':    wrist.tolist(),
        'handDir':  hand_dir.tolist(),
        'palm':     palm.tolist(),
        'hip':      femoral_head(fem).tolist(),
        'knee':     end_centroid(fem, False, 0.02).tolist(),
        'ankle':    end_centroid(tib, False, 0.02).tolist(),
    }
joints = {'R': joints_for('R'), 'L': joints_for('L')}

# ── 6. 簡化＋量化＋打包 ───────────────────────────────────────
CAP = {'m': 2600, 'b': 1400, 's': 28000}
KEEP_RATIO = {'m': 0.55, 'b': 0.5, 's': 0.65}      # 皮膚是外觀，留多一點三角形才平滑

selected = []
missing_zh = []
for p in atlas['parts']:
    if DROP.search(p['name']): continue
    g = group_of(p)
    if g is None: continue
    name_zh = zh(p['name'])
    if name_zh is None:
        missing_zh.append(p['name']); continue
    selected.append((p, g, name_zh))

if missing_zh:
    print('⚠️ 沒有中文名、故未收入：', len(missing_zh))
    for n in sorted(missing_zh): print('   ', n)

blob = bytearray()
parts_out = []
all_pos = []
stats = {}
def pad4():
    while len(blob) % 4: blob.append(0)

def weld(pos, idx):
    # ⚠️ 來源三角形在接縫處各自有一份頂點（V≈T），不先焊起來簡化就會把接縫撕開
    key = np.round(pos * 1e5).astype(np.int64)
    _, first, inverse = np.unique(key, axis=0, return_index=True, return_inverse=True)
    idx2 = inverse.reshape(-1)[idx]
    keep = (idx2[:,0] != idx2[:,1]) & (idx2[:,1] != idx2[:,2]) & (idx2[:,0] != idx2[:,2])
    return pos[first], idx2[keep]

decimated = []
for p, g, name_zh in selected:
    pos, idx = weld(*geometry(p))
    n_tri = len(idx)
    target = min(n_tri, max(200, min(CAP[g], int(n_tri * KEEP_RATIO[g]))))
    if target < n_tri:
        pos2, idx2 = fast_simplification.simplify(pos, idx, target_reduction=1 - target / n_tri)
        if len(idx2) < 40:  # 簡化壞掉就用原檔
            pos2, idx2 = pos, idx
    else:
        pos2, idx2 = pos, idx
    # 去掉沒用到的頂點
    used = np.unique(idx2)
    remap = -np.ones(len(pos2), dtype=np.int64); remap[used] = np.arange(len(used))
    pos2 = pos2[used]; idx2 = remap[idx2]
    assert len(pos2) < 65536, p['name']
    decimated.append((p, g, name_zh, pos2, idx2))
    all_pos.append(pos2)

lo = np.min(np.vstack(all_pos), axis=0); hi = np.max(np.vstack(all_pos), axis=0)
scale = (hi - lo)

for p, g, name_zh, pos2, idx2 in decimated:
    q = np.round((pos2 - lo) / scale * 65535.0 - 32768.0).clip(-32768, 32767).astype('<i2')
    pad4(); po = len(blob); blob.extend(q.tobytes())
    pad4(); io = len(blob); blob.extend(idx2.astype('<u2').tobytes())
    parts_out.append({
        'id': p['id'], 'en': p['name'], 'zh': name_zh, 'g': g, 'side': side_of(p['name']),
        'seg': bone_seg(p['name']) if g == 'b' else None,
        'region': region_of(p['name'], g),
        'v': int(len(pos2)), 't': int(len(idx2)), 'po': po, 'io': io,
    })
    s = stats.setdefault(g, [0,0,0]); s[0]+=1; s[1]+=len(pos2); s[2]+=len(idx2)

manifest = {
    'source': 'BodyParts3D 4.0 (DBCLS, CC BY 4.0) via human-atlas (MIT)',
    'bbox': [lo.tolist(), hi.tolist()],
    'joints': joints,
    'parts': parts_out,
}
(HERE / 'atlas.json').write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')))
(HERE / 'atlas.bin').write_bytes(bytes(blob))

b64 = base64.b64encode(bytes(blob)).decode('ascii')
tpl = (HERE / 'template.html').read_text()
assert '__MANIFEST__' in tpl and '__BLOB__' in tpl
html = tpl.replace('__MANIFEST__', json.dumps(manifest, ensure_ascii=False, separators=(',', ':'))).replace('__BLOB__', b64)
out = HERE.parent / 'body-3d.html'
out.write_text(html)

print('關節', json.dumps(joints, indent=1))
print('bbox', lo, hi)
for g, (n, v, t) in stats.items(): print(f'{g}: parts={n} verts={v} tris={t}')
print(f'blob {len(blob)/1e6:.2f} MB → base64 {len(b64)/1e6:.2f} MB → html {out.stat().st_size/1e6:.2f} MB')
