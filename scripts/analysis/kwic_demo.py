# -*- coding: utf-8 -*-
"""Layer 2 시범: 환상·실재 KWIC(문장단위 콘코던스) + 키워드별 '개념 태깅 비율'.
표면형 카운팅의 의미 모호성을 TEI term-태그로 검증한다."""
import os, glob, html, xml.etree.ElementTree as ET
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
def period(y):
    return "P1" if y <= 2006 else "P2" if y <= 2009 else "P3" if y <= 2012 else "P4"
def txt(el): return "".join(el.itertext())

AMBIG = ["환상", "실재", "정치", "감각", "사건", "윤리", "타자", "주체"]
KWIC_KW = ["환상", "실재"]

docs = []
for fp in sorted(glob.glob(os.path.join(SRC, "*.xml"))):
    fn = os.path.basename(fp); author, y = meta(fn)
    if y == 0: continue
    try: body = ET.parse(fp).getroot().find(f"{NS}text/{NS}body")
    except Exception: continue
    if body is None: continue
    docs.append((author, y, period(y), body))

# 1) 키워드별 raw vs 개념태깅 비율
print("keyword       raw   tagged  ratio   (P2 raw/tagged)")
summary = []
for kw in AMBIG:
    raw = tagged = p2raw = p2tag = 0
    for author, y, p, body in docs:
        raw += txt(body).count(kw)
        tg = sum(1 for t in body.iter(f"{NS}term") if kw in (t.text or ""))
        tagged += tg
        if p == "P2": p2raw += txt(body).count(kw); p2tag += tg
    ratio = tagged / raw if raw else 0
    summary.append((kw, raw, tagged, ratio, p2raw, p2tag))
    print(f"{kw:<10}{raw:>6}{tagged:>8}{ratio:>7.0%}     {p2raw}/{p2tag}")

# 2) KWIC (문장단위) — 환상/실재
def kwic_rows(kw):
    rows = ""
    n = 0
    for author, y, p, body in docs:
        for s in body.iter(f"{NS}s"):
            st = txt(s).strip()
            if kw in st:
                tg = any(kw in (t.text or "") for t in s.iter(f"{NS}term"))
                hl = html.escape(st).replace(kw, f"<mark>{kw}</mark>")
                badge = "<span class='tg'>개념태깅</span>" if tg else "<span class='ut'>비태깅</span>"
                rows += (f"<tr class='r {p}' data-kw='{kw}'><td>{html.escape(author)}<br>"
                         f"<span class='mut'>{y} {p}</span></td><td>{badge} {hl}</td></tr>")
                n += 1
    return rows, n

CSS = """body{font-family:'Malgun Gothic',sans-serif;max-width:1000px;margin:0 auto;padding:22px;color:#1f2937}
h1{font-size:20px}h2{font-size:15px;margin-top:24px;color:#4338ca}
table{border-collapse:collapse;width:100%;font-size:12.5px;margin:8px 0}
td,th{border:1px solid #e5e7eb;padding:5px 8px}th{background:#f8fafc}
td:first-child{white-space:nowrap}.mut{color:#9ca3af;font-size:10.5px}
mark{background:#fde68a;padding:0 1px}.lead{color:#6b7280;font-size:12px}
.tg{font-size:9.5px;background:#dcfce7;color:#15803d;padding:1px 5px;border-radius:8px}
.ut{font-size:9.5px;background:#fee2e2;color:#b91c1c;padding:1px 5px;border-radius:8px}
.st{border-collapse:collapse;font-size:12.5px;margin:6px 0}.st td,.st th{border:1px solid #e5e7eb;padding:4px 10px;text-align:center}
.bar{display:inline-block;height:11px;background:#10b981;border-radius:2px;vertical-align:middle}
input{padding:6px 9px;border:1px solid #d1d5db;border-radius:6px;width:280px;margin:4px 6px 4px 0}
button{padding:5px 10px;border:1px solid #c7d2fe;background:#eef2ff;border-radius:6px;cursor:pointer;font-size:12px}"""
strows = ""
for kw, raw, tagged, ratio, p2r, p2t in summary:
    strows += (f"<tr><td>{html.escape(kw)}</td><td>{raw}</td><td>{tagged}</td>"
               f"<td><span class='bar' style='width:{int(ratio*120)}px'></span> {ratio:.0%}</td>"
               f"<td>{p2r}/{p2t}</td></tr>")
r1, n1 = kwic_rows("환상"); r2, n2 = kwic_rows("실재")
doc = f"""<!doctype html><meta charset='utf-8'><style>{CSS}</style>
<h1>Layer 2 시범 — 환상·실재 KWIC + 개념 태깅 비율</h1>
<h2>① 표면형 카운팅의 검증 — 키워드별 '개념(term)으로 태깅된 비율'</h2>
<p class='lead'>비율이 높을수록 비평이 그 말을 <b>개념으로 사유</b>한 것(이론적 용법). 낮으면 일상적 용법 혼입 가능.</p>
<table class='st'><tr><th>키워드</th><th>표면 출현(raw)</th><th>개념 태깅수</th><th>태깅 비율</th><th>P2 raw/tagged</th></tr>{strows}</table>
<h2>② 환상·실재 KWIC ({n1}+{n2}건) — P2(2007–09)가 이론적 정점인지 직접 읽기</h2>
<div><input id='q' placeholder='🔍 문장 필터'>
<button onclick="flt('all')">전체</button> <button onclick="flt('P2')">P2만</button>
<button onclick="kw('환상')">환상</button> <button onclick="kw('실재')">실재</button></div>
<table id='t'><tr><th>저자</th><th>문장</th></tr>{r1}{r2}</table>
<script>
let pf='all',kf='all';
function ap(){{document.querySelectorAll('#t .r').forEach(r=>{{
 const okp=(pf=='all'||r.classList.contains(pf)),okk=(kf=='all'||r.dataset.kw==kf),
 okq=(!q.value||r.textContent.includes(q.value));
 r.style.display=(okp&&okk&&okq)?'':'none';}});}}
function flt(p){{pf=p;ap();}} function kw(k){{kf=k;ap();}}
document.getElementById('q').oninput=ap;
</script>"""
open(os.path.join(OUT, "kwic_환상_실재.html"), "w", encoding="utf-8").write(doc)
print("\nKWIC: 환상", n1, "/ 실재", n2, "-> kwic_환상_실재.html")
