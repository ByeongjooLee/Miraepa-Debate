# -*- coding: utf-8 -*-
"""H4 (2층 emic 설계): 담론 자기어휘의 '개념(term-태깅) 빈도' 통시 궤적
 + 부재/주변어(최종환 틀)를 별도 보고. + H1 경쟁 명명어(표면빈도).
정규화 = 만 자(공백 제외)당. 분산 = 문서빈도."""
import os, glob, csv, html, xml.etree.ElementTree as ET
from collections import defaultdict

NS = "{http://www.tei-c.org/ns/1.0}"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mirea_results")
OUT = os.path.join(HERE, "미래파_분석_확장")
YEAR_FIX = {"박상수_무한": 2010, "이병철_감각적 허상": 2014, "조재룡_주체에서 주체로": 2013}

def meta(fn):
    b = fn[:-4]
    if b.endswith("_v2"): b = b[:-3]
    ps = b.split("_"); y = next((int(p) for p in ps if p.isdigit() and len(p) == 4), 0)
    if y == 0:
        for k, v in YEAR_FIX.items():
            if fn.startswith(k): y = v; break
    return ps[0], y
def txt(el): return "".join(el.itertext())
def period(y):
    return ("P1 2005-06\n발생·명명" if y <= 2006 else "P2 2007-09\n이론화·전개"
            if y <= 2009 else "P3 2010-12\n회고·특집" if y <= 2012 else "P4 2013-24\n재평가·이후")
PORDER = ["P1 2005-06\n발생·명명", "P2 2007-09\n이론화·전개", "P3 2010-12\n회고·특집", "P4 2013-24\n재평가·이후"]

# 2층 키워드
CORE = ["환상", "실재", "타자", "주체", "윤리", "정치", "감각", "전복", "사건", "서정"]  # 담론 자기어휘 → 개념(term)빈도
MARGINAL = ["메시아", "부정성", "주이상스", "숭고"]                                      # 최종환 틀 / 부재·주변 → 표면빈도로 부재 확인
H1 = ["미래파", "다른 서정", "뉴웨이브", "신서정", "아방가르드", "모더니즘"]              # 명명 → 표면빈도

docs = []
for fp in sorted(glob.glob(os.path.join(SRC, "*.xml"))):
    fn = os.path.basename(fp); a, y = meta(fn)
    if y == 0: continue
    try: body = ET.parse(fp).getroot().find(f"{NS}text/{NS}body")
    except Exception: continue
    if body is None: continue
    t = txt(body)
    terms = [(tt.text or "") for tt in body.iter(f"{NS}term")]
    docs.append(dict(a=a, y=y, p=period(y), t=t,
                     chars=len(t.replace(" ", "").replace("\n", "").replace("\t", "")), terms=terms))

pchars = {p: sum(d["chars"] for d in docs if d["p"] == p) for p in PORDER}
pdocs = {p: sum(1 for d in docs if d["p"] == p) for p in PORDER}

def tagged_count(d, kw): return sum(1 for tm in d["terms"] if kw in tm)
def raw_count(d, kw): return d["t"].count(kw)

def aggregate(keywords, mode):  # mode: 'tagged' or 'raw'
    rate, dfreq = defaultdict(dict), defaultdict(dict)
    for kw in keywords:
        for p in PORDER:
            sel = [d for d in docs if d["p"] == p]
            occ = sum((tagged_count if mode == "tagged" else raw_count)(d, kw) for d in sel)
            df = sum(1 for d in sel if (tagged_count if mode == "tagged" else raw_count)(d, kw) > 0)
            rate[kw][p] = round(occ / pchars[p] * 10000, 2) if pchars[p] else 0
            dfreq[kw][p] = df
    return rate, dfreq

coreR, coreD = aggregate(CORE, "tagged")
h1R, h1D = aggregate(H1, "raw")
margR, margD = aggregate(MARGINAL, "raw")  # 부재 확인은 표면빈도로(가장 너그럽게 잡아도 없음을 보이기 위해)

# CSV
with open(os.path.join(OUT, "h4_keyword_trajectory.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["층", "키워드", "측정"] + [p.replace("\n", " ") for p in PORDER] + ["문서빈도(P1..P4)"])
    for kw in CORE:
        w.writerow(["자기어휘", kw, "개념태깅/만자"] + [coreR[kw][p] for p in PORDER]
                   + [" ".join(f"{coreD[kw][p]}/{pdocs[p]}" for p in PORDER)])
    for kw in MARGINAL:
        w.writerow(["주변/부재", kw, "표면/만자"] + [margR[kw][p] for p in PORDER]
                   + [" ".join(f"{margD[kw][p]}/{pdocs[p]}" for p in PORDER)])
    for kw in H1:
        w.writerow(["명명", kw, "표면/만자"] + [h1R[kw][p] for p in PORDER]
                   + [" ".join(f"{h1D[kw][p]}/{pdocs[p]}" for p in PORDER)])

# HTML
def heat(kws, rate, df):
    rows = ""
    for kw in kws:
        mx = max(rate[kw].values()) or 1
        cells = ""
        for p in PORDER:
            v = rate[kw][p]; it = v / mx
            cells += (f"<td style='background:rgba(79,70,229,{0.06+it*0.84:.2f});"
                      f"color:{'#fff' if it>0.55 else '#1f2937'}'>{v}"
                      f"<div class='df'>{df[kw][p]}/{pdocs[p]}</div></td>")
        peak = max(PORDER, key=lambda p: rate[kw][p]).split("\n")[0]
        rows += f"<tr><th>{html.escape(kw)}</th>{cells}<td class='pk'>{peak}</td></tr>"
    return rows
heads = "".join(f"<th>{p.split(chr(10))[0]}<br><span class='sub'>{p.split(chr(10))[1]} · n={pdocs[p]}</span></th>" for p in PORDER)

CSS = """body{font-family:'Malgun Gothic',sans-serif;max-width:920px;margin:0 auto;padding:24px;color:#1f2937}
h1{font-size:20px}h2{font-size:15px;margin-top:26px;color:#4338ca}
table{border-collapse:collapse;width:100%;font-size:12.5px;margin:8px 0}
td,th{border:1px solid #e5e7eb;padding:6px 8px;text-align:center}th{background:#f8fafc}
td:first-child,th:first-child{text-align:left}td{font-weight:600}
.sub{font-weight:400;color:#9ca3af;font-size:9px}.df{font-size:9px;font-weight:400;opacity:.75}
.pk{background:#fef9c3;font-size:11px}
.lead{color:#6b7280;font-size:12px}.box{border-left:4px solid #6366f1;background:#f8fafc;padding:10px 14px;font-size:12.5px;margin:12px 0}
.warn{border-left-color:#ef4444;background:#fef2f2}"""
margtbl = "".join(
    f"<tr><th>{html.escape(kw)}</th>" + "".join(f"<td>{margR[kw][p]}<div class='df'>{margD[kw][p]}/{pdocs[p]}</div></td>" for p in PORDER) + "</tr>"
    for kw in MARGINAL)
doc = f"""<!doctype html><meta charset='utf-8'><style>{CSS}</style>
<h1>H4 (2층 emic) — 미래파 담론의 자기어휘 궤적 + 부재어</h1>
<p class='lead'>P1 발생·명명 → P2 이론화 → P3 회고·특집 → P4 재평가·이후 · 색=행 내부 상대강도 · 작은수=문서빈도 · 노랑=정점</p>

<h2>① 담론 자기어휘 — '개념(term)으로 태깅된' 빈도 / 만자 <span class='lead'>(표면빈도 아님 → 일상적 용법 제거)</span></h2>
<table><tr><th>개념어</th>{heads}<th>정점</th></tr>{heat(CORE, coreR, coreD)}</table>

<h2>② 명명어(표면빈도/만자)</h2>
<table><tr><th>명명어</th>{heads}<th>정점</th></tr>{heat(H1, h1R, h1D)}</table>

<div class='box warn'><b>③ 주변·부재어 — 최종환의 분석 틀이나 코퍼스엔 거의 없음 (표면빈도/만자)</b><br>
<table style='margin-top:6px'><tr><th>키워드</th>{''.join(f'<th>{p.split(chr(10))[0]}</th>' for p in PORDER)}</tr>{margtbl}</table>
<span class='lead'>메시아=전 시기 0. 부정성·주이상스·숭고도 거의 부재. → <b>담론의 자기어휘가 아니라 연구자(최종환)의 해석 틀</b>(또는 그의 근거가 시비평 코퍼스 밖). 이 간극 자체가 발견이다.</span></div>

<p class='lead'>총 {len(docs)}편 · 자기어휘는 개념태깅 기준이므로 표면빈도보다 작고, 사건이 자동 강등됨(일상 용법 제거).</p>"""
open(os.path.join(OUT, "h4_keyword_trajectory.html"), "w", encoding="utf-8").write(doc)
print("docs", len(docs), "OK")
