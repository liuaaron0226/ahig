import json, re
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
jent=j['entries']
pats={
 '檢索雜訊': r'檢索雜訊(?:累計)?第 (\d+) 筆',
 '自選補給': r'自選補給型?(?:累計)?第 (\d+) 筆',
 '青少年': r'青少年(?:排除)?(?:累計)?第 (\d+) 筆',
 '學位論文': r'(?:學位論文|博士論文)(?:累計)?第 (\d+) (?:筆|篇)',
 '預印本': r'預印本(?:累計)?第 (\d+) 筆',
 '漱口': r'漱口(?:研究)?(?:累計)?第 (\d+) 筆',
 'running詞族': r'`running` 詞族誤命中第 (\d+) 筆',
 'cycle詞族': r'`cycle` 詞族誤命中第 (\d+) 筆',
 'carbohydrate詞族': r'`carbohydrate` 詞族誤命中第 (\d+) 筆',
 'endurance詞族': r'`endurance` 詞族誤命中第 (\d+) 筆',
 '去重第四型': r'(?:去重|重複).{0,12}第(?:四|4)型.{0,8}第 (\d+) 例',
 '去重第五型': r'(?:去重|重複).{0,12}第(?:五|5)型.{0,8}第 (\d+) 例',
 '真實攝取': r'真實(?:世界)?攝取.{0,10}第 (\d+) 筆',
}
for name,p in pats.items():
    last=None; n=0
    for e in jent:
        for m in re.finditer(p, e['reason']):
            last=(int(m.group(1)), e['candidateId'][-8:]); n+=1
    print(f'{name}: last={last} occurrences={n}')
