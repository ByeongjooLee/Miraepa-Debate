# -*- coding: utf-8 -*-
"""담화 운율(discourse prosody) 시범: '미래파' 문장 곁의 긍정/부정 평가어 공기를 시기별로."""
import os, glob, xml.etree.ElementTree as ET
from collections import Counter, defaultdict

NS = "{http://www.tei-c.org/ns/1.0}"
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mirea_results")
YEAR_FIX = {"박상수_무한": 2010, "이병철_감각적 허상": 2014, "조재룡_주체에서 주체로": 2013}
def meta(fn):
    b = fn[:-4]
    if b.endswith("_v2"): b = b[:-3]
    ps = b.split("_"); y = next((int(p) for p in ps if p.isdigit() and len(p) == 4), 0)
    if y == 0:
        for k, v in YEAR_FIX.items():
            if fn.startswith(k): y = v; break
    return y
def txt(el): return "".join(el.itertext())
def period(y):
    return "I 발생·논쟁(05-07)" if y<=2007 else "II 분기·이론화(08-09)" if y<=2009 else "III 정리(10-11)" if y<=2011 else "IV 사후 역사화(13-24)"
PORDER=["I 발생·논쟁(05-07)","II 분기·이론화(08-09)","III 정리(10-11)","IV 사후 역사화(13-24)"]

# 평가어 사전(어근 substring) — 이 담론에서 '미래파'를 향하기 쉬운 말 위주(증거 시범용)
POS = ["새로","대안","가능성","신선","참신","활력","혁신","갱신","주목"]
NEG = ["난해","폐쇄","자폐","소모","모호","허상","외설","장광설","유희","혼란","과잉","실패"]

byp_pos=defaultdict(Counter); byp_neg=defaultdict(Counter); byp_n=Counter()
kwic=defaultdict(list)
for fp in sorted(glob.glob(os.path.join(SRC,"*.xml"))):
    y=meta(os.path.basename(fp))
    if not y: continue
    try: body=ET.parse(fp).getroot().find(f"{NS}text/{NS}body")
    except Exception: continue
    if body is None: continue
    p=period(y)
    for s in body.iter(f"{NS}s"):
        st=txt(s)
        if "미래파" not in st: continue
        byp_n[p]+=1
        hp=[w for w in POS if w in st]; hn=[w for w in NEG if w in st]
        for w in hp: byp_pos[p][w]+=1
        for w in hn: byp_neg[p][w]+=1
        if (hp or hn) and len(kwic[p])<4:
            kwic[p].append(("+"+",".join(hp)+" -"+",".join(hn), st[:90].strip()))

out=["[ '미래파' 문장의 담화 운율 — 시기별 ]","","%-22s %6s %6s %6s %8s"%("시기","문장수","긍정","부정","운율지수")]
for p in PORDER:
    pos=sum(byp_pos[p].values()); neg=sum(byp_neg[p].values()); n=byp_n[p]
    idx=(pos-neg)/(pos+neg) if (pos+neg) else 0
    out.append("%-22s %6d %6d %6d %+8.2f"%(p,n,pos,neg,idx))
out.append("\n(운율지수 = (긍정-부정)/(긍정+부정), +1=완전긍정 ~ -1=완전부정)")
out.append("\n[ 시기별 자주 나온 평가어 ]")
for p in PORDER:
    out.append("· %s"%p)
    out.append("   긍정: "+", ".join("%s×%d"%(w,c) for w,c in byp_pos[p].most_common(6)))
    out.append("   부정: "+", ".join("%s×%d"%(w,c) for w,c in byp_neg[p].most_common(6)))
out.append("\n[ KWIC 예시(평가어 포함 문장) ]")
for p in PORDER:
    for tag,s in kwic[p][:2]:
        out.append("  [%s] (%s) %s..."%(p.split()[0],tag,s))
open("_prosody.txt","w",encoding="utf-8").write("\n".join(out))
print("OK")
