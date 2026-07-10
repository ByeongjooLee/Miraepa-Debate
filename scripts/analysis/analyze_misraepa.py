# -*- coding: utf-8 -*-
"""미래파 담론 분석:
 Q1 미래파 용어의 비평가별 전유(명명 분포·경쟁 명명어·공기 개념어·용례 concordance)
 Q2 비평가별 평가 성향(긍/중/부) + 미래파 근접 평가
 Q3 시기별 담론 변화
산출: 미래파_분석/  (CSV 4종 + 리포트.html)
"""
import os, sys, glob, csv, re, html, xml.etree.ElementTree as ET
from collections import Counter, defaultdict

NS = "{http://www.tei-c.org/ns/1.0}"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, "미래파")
OUT = os.path.join(HERE, sys.argv[2]) if len(sys.argv) > 2 else os.path.join(HERE, "미래파_분석")
os.makedirs(OUT, exist_ok=True)
KEY = "미래파"

def ln(t): return t.split("}", 1)[-1] if "}" in t else t
def txt(el): return "".join(el.itertext())
def esc(s): return html.escape(str(s) if s is not None else "")

YEAR_FIX = {  # 파일명이 잘려 연도가 누락된 글 보정 (PDF_처리분류.md 기준)
    "박상수_무한": 2010,
    "이병철_감각적 허상": 2014,
    "조재룡_주체에서 주체로": 2013,
}

def parse_meta(fname):
    base = fname[:-4]
    if base.endswith("_v2"): base = base[:-3]
    parts = base.split("_")
    author = parts[0]
    year = next((int(p) for p in parts if p.isdigit() and len(p) == 4), 0)
    if year == 0:
        for k, v in YEAR_FIX.items():
            if fname.startswith(k):
                year = v; break
    journal = ""
    if len(parts) >= 3:
        journal = parts[-2] if parts[-1].isdigit() else parts[-1]
    return author, year, journal

# ---------- 추출 ----------
docs = []
for fp in sorted(glob.glob(os.path.join(SRC, "*.xml"))):
    fn = os.path.basename(fp)
    author, year, journal = parse_meta(fn)
    try:
        root = ET.parse(fp).getroot()
    except Exception as e:
        print("PARSE-FAIL:", fn, "::", e)
        continue
    t_el = root.find(f"{NS}teiHeader/{NS}fileDesc/{NS}titleStmt/{NS}title")
    title = (t_el.text if t_el is not None else fn).strip()
    body = root.find(f"{NS}text/{NS}body")
    d = dict(author=author, year=year, journal=journal, fname=fn, title=title,
             n_key=0, interp=Counter(), interp_near=Counter(),
             movement=Counter(), concept=Counter(), cooc=Counter(),
             key_sents=[])
    if body is None:
        docs.append(d); continue
    d["n_key"] = txt(body).count(KEY)
    # 전체 term / interp
    for el in body.iter():
        n = ln(el.tag)
        if n == "term":
            tt = el.get("type", "")
            s = (el.text or "").strip()
            if not s: continue
            if tt == "movement":
                d["movement"][s] += 1
            else:
                d["concept"][s] += 1
        elif n == "interp":
            d["interp"][el.get("value", "?")] += 1
    # 문단 단위: 미래파 근접 interp + 문장 단위 공기어/용례
    for p in body.iter(f"{NS}p"):
        ptext = txt(p)
        p_has = KEY in ptext
        if p_has:
            for itp in p.iter(f"{NS}interp"):
                d["interp_near"][itp.get("value", "?")] += 1
        for s in p.iter(f"{NS}s"):
            stext = txt(s).strip()
            if KEY in stext:
                # 같은 문장 내 개념어 공기
                co = []
                for term in s.iter(f"{NS}term"):
                    tv = (term.text or "").strip()
                    if tv and KEY not in tv:
                        co.append(tv)
                        d["cooc"][tv] += 1
                # 문장 내 평가
                vals = [itp.get("value", "") for itp in s.iter(f"{NS}interp")]
                d["key_sents"].append(dict(text=stext, cooc=co, vals=vals))
    docs.append(d)

def role(n):
    return "핵심 명명" if n >= 5 else ("부분 언급" if n >= 1 else "비명명(대상비평)")

# ---------- CSV ----------
def w(name, header, rows):
    with open(os.path.join(OUT, name), "w", encoding="utf-8-sig", newline="") as f:
        wr = csv.writer(f); wr.writerow(header); wr.writerows(rows)

# 1) 비평가 요약
w("critic_summary.csv",
  ["저자", "연도", "매체", "미래파언급", "역할", "interp_긍정", "interp_중립", "interp_비판",
   "긍정비율", "근접_긍정", "근접_중립", "근접_비판", "글제목"],
  [[d["author"], d["year"], d["journal"], d["n_key"], role(d["n_key"]),
    d["interp"]["affirmative"], d["interp"]["neutral"], d["interp"]["critical"],
    round(d["interp"]["affirmative"] / max(1, sum(d["interp"].values())), 3),
    d["interp_near"]["affirmative"], d["interp_near"]["neutral"], d["interp_near"]["critical"],
    d["title"]] for d in docs])

# 2) concordance (미래파 용례)
conc_rows = []
for d in docs:
    for ks in d["key_sents"]:
        conc_rows.append([d["author"], d["year"], d["journal"],
                          ks["text"], " | ".join(ks["cooc"]), " ".join(ks["vals"])])
w("concordance_미래파.csv",
  ["저자", "연도", "매체", "용례문장", "공기개념어", "문장내평가"], conc_rows)

# 3) 경쟁 명명어 매트릭스 (movement terms)
all_mv = Counter()
for d in docs: all_mv.update(d["movement"])
mv_terms = [t for t, _ in all_mv.most_common()]
w("movement_terms.csv",
  ["저자", "연도"] + mv_terms,
  [[d["author"], d["year"]] + [d["movement"].get(t, 0) for t in mv_terms] for d in docs])

# 4) 미래파 공기 개념어 (전체 + 비평가별)
glob_cooc = Counter()
for d in docs: glob_cooc.update(d["cooc"])
w("cooccurrence_미래파.csv",
  ["개념어", "전체빈도"] + [d["author"] for d in docs if d["n_key"] > 0],
  [[t, c] + [d["cooc"].get(t, 0) for d in docs if d["n_key"] > 0]
   for t, c in glob_cooc.most_common()])

# ---------- HTML 리포트 ----------
def hbar(val, maxv, color, w=260):
    px = int(round(val / maxv * w)) if maxv else 0
    return f"<span class='bar' style='width:{px}px;background:{color}'></span><span class='bv'>{val}</span>"

def stance_bar(a, n, c, w=220):
    tot = a + n + c
    if not tot: return "<span class='muted'>—</span>"
    pa, pn, pc = [int(round(x / tot * w)) for x in (a, n, c)]
    return (f"<span class='sbar'><span style='width:{pa}px;background:#34d399'></span>"
            f"<span style='width:{pn}px;background:#cbd5e1'></span>"
            f"<span style='width:{pc}px;background:#f87171'></span></span>"
            f"<span class='bv'>{a}·{n}·{c}</span>")

# 코퍼스 개요
rows_overview = ""
for d in sorted(docs, key=lambda x: (x["year"], x["author"])):
    rows_overview += (f"<tr><td>{esc(d['author'])}</td><td>{d['year']}</td><td>{esc(d['journal'])}</td>"
                      f"<td style='text-align:right'>{d['n_key']}</td><td>{role(d['n_key'])}</td>"
                      f"<td>{stance_bar(d['interp']['affirmative'],d['interp']['neutral'],d['interp']['critical'])}</td>"
                      f"<td class='ti'>{esc(d['title'])}</td></tr>")

# Q1-a 명명 분포
named = [d for d in docs if d["n_key"] > 0]
maxkey = max((d["n_key"] for d in docs), default=1)
q1a = ""
for d in sorted(named, key=lambda x: -x["n_key"]):
    q1a += (f"<tr><td>{esc(d['author'])} <span class='muted'>{d['year']}</span></td>"
            f"<td>{hbar(d['n_key'], maxkey, '#6366f1')}</td></tr>")

# Q1-b 경쟁 명명어 매트릭스
mv_top = [t for t, _ in all_mv.most_common(12)]
q1b_head = "".join(f"<th class='rot'>{esc(t)}</th>" for t in mv_top)
q1b = ""
for d in sorted(docs, key=lambda x: (x["year"], x["author"])):
    cells = ""
    for t in mv_top:
        v = d["movement"].get(t, 0)
        bg = f"background:rgba(99,102,241,{min(0.85,0.18+v*0.12)})" if v else ""
        cells += f"<td style='{bg}'>{v or ''}</td>"
    q1b += f"<tr><td class='lbl'>{esc(d['author'])} <span class='muted'>{d['year']}</span></td>{cells}</tr>"

# Q1-c 공기 개념어 top
maxco = glob_cooc.most_common(1)[0][1] if glob_cooc else 1
q1c = ""
for t, c in glob_cooc.most_common(20):
    q1c += f"<tr><td>{esc(t)}</td><td>{hbar(c, maxco, '#10b981')}</td></tr>"

# Q1-d concordance (검색 가능)
conc_html = ""
for d in sorted(named, key=lambda x: (x["year"], x["author"])):
    for ks in d["key_sents"]:
        hl = esc(ks["text"]).replace(KEY, f"<mark>{KEY}</mark>")
        vtag = ""
        for v in ks["vals"]:
            cmap = {"affirmative": "긍", "neutral": "중", "critical": "부"}
            if v in cmap: vtag += f"<span class='vchip v-{v}'>{cmap[v]}</span>"
        conc_html += (f"<tr class='crow'><td class='nowrap'>{esc(d['author'])}<br><span class='muted'>{d['year']}</span></td>"
                      f"<td>{hl} {vtag}<div class='co'>{esc(' · '.join(ks['cooc']))}</div></td></tr>")

# Q2 비평가별 stance (전체)
q2 = ""
for d in sorted(docs, key=lambda x: -(x["interp"]["affirmative"] / max(1, sum(x["interp"].values())))):
    tot = sum(d["interp"].values())
    ratio = f"{d['interp']['affirmative']/max(1,tot)*100:.0f}%" if tot else "—"
    q2 += (f"<tr><td>{esc(d['author'])} <span class='muted'>{d['year']}</span></td>"
           f"<td>{stance_bar(d['interp']['affirmative'],d['interp']['neutral'],d['interp']['critical'])}</td>"
           f"<td class='muted' style='text-align:right'>긍정 {ratio}</td></tr>")

# Q2-b 미래파 근접 stance (명명 비평가)
q2b = ""
for d in sorted(named, key=lambda x: (x["year"], x["author"])):
    nn = d["interp_near"]
    q2b += (f"<tr><td>{esc(d['author'])} <span class='muted'>{d['year']}</span></td>"
            f"<td>{stance_bar(nn['affirmative'],nn['neutral'],nn['critical'])}</td></tr>")

# Q3 연도별 집계
by_year = defaultdict(lambda: dict(n_key=0, texts=0, a=0, n=0, c=0))
for d in docs:
    y = by_year[d["year"]]
    y["n_key"] += d["n_key"]; y["texts"] += 1
    y["a"] += d["interp"]["affirmative"]; y["n"] += d["interp"]["neutral"]; y["c"] += d["interp"]["critical"]
years = sorted(by_year)
maxykey = max((by_year[y]["n_key"] for y in years), default=1)
q3a = ""
for y in years:
    yy = by_year[y]
    q3a += (f"<tr><td>{y}</td><td class='muted'>{yy['texts']}편</td>"
            f"<td>{hbar(yy['n_key'], maxykey, '#6366f1')}</td>"
            f"<td>{stance_bar(yy['a'],yy['n'],yy['c'])}</td></tr>")

# Q3 타임라인 산점도 (연도 x 긍정비율) SVG
W, H, PAD = 720, 300, 44
xmin, xmax = min(years), max(years)
def sx(y): return PAD + (y - xmin) / max(1, (xmax - xmin)) * (W - 2 * PAD)
def sy(r): return H - PAD - r * (H - 2 * PAD)
pts = ""
for d in docs:
    tot = sum(d["interp"].values())
    if not tot: continue
    r = d["interp"]["affirmative"] / tot
    x, y = sx(d["year"]), sy(r)
    big = d["n_key"] > 0
    pts += (f"<circle cx='{x:.0f}' cy='{y:.0f}' r='{6 if big else 4}' "
            f"fill='{'#6366f1' if big else '#cbd5e1'}' opacity='.85'><title>{esc(d['author'])} {d['year']} 긍정{r*100:.0f}% 미래파{d['n_key']}회</title></circle>"
            f"<text x='{x+8:.0f}' y='{y+3:.0f}' class='pt'>{esc(d['author'])}</text>")
gx = ""
for y in range(xmin, xmax + 1, 2):
    gx += f"<line x1='{sx(y):.0f}' y1='{PAD-10}' x2='{sx(y):.0f}' y2='{H-PAD}' class='grid'/><text x='{sx(y):.0f}' y='{H-PAD+16}' class='ax' text-anchor='middle'>{y}</text>"
gy = ""
for r in (0, .25, .5, .75, 1):
    gy += f"<line x1='{PAD}' y1='{sy(r):.0f}' x2='{W-PAD}' y2='{sy(r):.0f}' class='grid'/><text x='{PAD-8}' y='{sy(r)+3:.0f}' class='ax' text-anchor='end'>{int(r*100)}%</text>"
scatter = f"<svg viewBox='0 0 {W} {H}' class='chart'>{gy}{gx}{pts}</svg>"

CSS = """
body{font-family:'Malgun Gothic',system-ui,sans-serif;color:#1f2937;max-width:1000px;margin:0 auto;padding:30px 26px;line-height:1.6}
h1{font-size:25px;margin:0 0 4px}h2{font-size:19px;margin:38px 0 6px;padding-top:14px;border-top:2px solid #eef2ff}
h3{font-size:15px;margin:22px 0 8px;color:#4338ca}
.lead{color:#6b7280;font-size:13.5px;margin:0 0 8px}
table{border-collapse:collapse;font-size:13px;margin:8px 0 6px;width:100%}
td,th{border:1px solid #e5e7eb;padding:5px 8px;vertical-align:middle}
th{background:#f8fafc;font-weight:600}
.bar{display:inline-block;height:12px;border-radius:3px;vertical-align:middle}
.bv{font-size:11.5px;color:#6b7280;margin-left:6px}
.sbar{display:inline-flex;height:13px;border-radius:3px;overflow:hidden;vertical-align:middle;width:220px;background:#f1f5f9}
.sbar span{display:block;height:100%}
.muted{color:#9ca3af;font-size:11.5px}.ti{font-size:12px;color:#475569}
.rot{height:90px;white-space:nowrap}.rot{writing-mode:vertical-rl;transform:rotate(180deg);font-weight:500;font-size:11.5px}
td.lbl{white-space:nowrap;font-size:12px}
mark{background:#fde68a;padding:0 1px}
.co{font-size:11px;color:#10b981;margin-top:2px}
.vchip{font-size:10px;padding:0 5px;border-radius:8px;margin-left:3px;color:#fff}
.v-affirmative{background:#10b981}.v-neutral{background:#94a3b8}.v-critical{background:#ef4444}
.chart{width:100%;height:auto;border:1px solid #eef2ff;border-radius:8px;background:#fff}
.grid{stroke:#eef2ff}.ax{font-size:10px;fill:#94a3b8}.pt{font-size:9px;fill:#475569}
.box{background:#f8fafc;border:1px solid #e5e7eb;border-left:4px solid #6366f1;border-radius:6px;padding:10px 14px;font-size:13px;margin:10px 0}
.note{background:#fffbeb;border-left-color:#f59e0b}
#csearch{width:100%;padding:7px 10px;border:1px solid #d1d5db;border-radius:7px;margin:6px 0;font-size:13px}
.legend{font-size:11.5px;color:#6b7280}
.legend i{display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:middle;margin:0 3px 0 10px}
"""
JS = """
const q=document.getElementById('csearch');
q.oninput=()=>{const v=q.value.trim();document.querySelectorAll('.crow').forEach(r=>{
 r.style.display=(!v||r.textContent.includes(v))?'':'none';});};
"""

leg = ("<div class='legend'>평가 막대: <i style='background:#34d399'></i>긍정"
       "<i style='background:#cbd5e1'></i>중립<i style='background:#f87171'></i>비판</div>")

doc_html = f"""<!doctype html><html lang='ko'><head><meta charset='utf-8'>
<title>미래파 담론 분석</title><style>{CSS}</style></head><body>
<h1>「미래파」 논쟁 담론 분석</h1>
<p class='lead'>대상: 미래파 관련 비평 {len(docs)}편 ({xmin}–{xmax}) · TEI 태깅 데이터 기반</p>

<div class='box'><b>코퍼스의 구조적 발견</b><br>
16편 중 <b>"미래파"를 직접 호명하는 글은 {len(named)}편</b>이며, 나머지 {len(docs)-len(named)}편은
미래파로 분류되는 시인을 다루되 그 명칭을 사용하지 않는다. 즉 코퍼스는
<b>① 미래파를 명명·이론화하는 메타담론</b>과 <b>② 명명 없이 대상 시를 비평하는 글</b>로 갈린다 —
이 분기 자체가 '미래파'가 사후적·외부적으로 부여된 범주임을 시사한다.</div>

<table><tr><th>저자</th><th>연도</th><th>매체</th><th>미래파</th><th>역할</th><th>평가성향(전체)</th><th>글제목</th></tr>
{rows_overview}</table>{leg}

<h2>Q1. '미래파' 용어의 비평가별 전유</h2>

<h3>① 명명 빈도 — 누가 이 용어를 적극 사용하는가</h3>
<table>{q1a}</table>

<h3>② 경쟁 명명어 지형 (movement 태그) — 각자 어떤 범주어를 선호하는가</h3>
<p class='lead'>'미래파'와 함께/대신 동원되는 사조·유파 명칭의 비평가별 분포</p>
<table><tr><td class='lbl'></td>{q1b_head}</tr>{q1b}</table>

<h3>③ '미래파' 공기(共起) 개념어 top 20 — 무엇과 결부되어 정의되는가</h3>
<table>{q1c}</table>

<h3>④ 용례 concordance (미래파 출현 문장 전체)</h3>
<input id='csearch' placeholder='🔍 단어로 용례 필터 (예: 환상, 정치, 주체...)'>
<table><tr><th class='nowrap'>저자</th><th>'미래파'가 쓰인 문장 <span class='muted'>(초록=공기 개념어, 칩=문장내 평가)</span></th></tr>
{conc_html}</table>

<h2>Q2. 비평가별 평가 성향 (긍정 / 중립 / 비판)</h2>
<div class='box note'><b>방법론 주의</b> — interp(평가) 태그는 '미래파' 단어에 직접 부착돼 있지 않다(직접 부착 1건).
따라서 아래는 ⓐ <b>글 전체의 평가 성향</b>과 ⓑ <b>미래파 언급 문단 근처의 평가</b>로 나누어 근사한 값이며,
'미래파에 대한 찬반'으로 곧장 등치할 수는 없다. 정밀 판정은 Q1-④ concordance를 함께 읽어야 한다.</div>

<h3>ⓐ 글 전체 평가 성향 (긍정비율 내림차순)</h3>
<table>{q2}</table>{leg}

<h3>ⓑ '미래파' 언급 문단 근처의 평가 (명명 비평가)</h3>
<table>{q2b}</table>

<h2>Q3. 시기별 담론 변화</h2>
<h3>① 연도별 미래파 언급량 · 평가성향</h3>
<table><tr><th>연도</th><th>편수</th><th>미래파 언급</th><th>평가성향</th></tr>{q3a}</table>

<h3>② 타임라인 — 연도(x) × 글의 긍정비율(y), ●=미래파 명명 / ○=비명명</h3>
{scatter}

<div class='box'>해석 가이드: 2005–2006 명명 이전의 대상비평(이장욱·신형철) → 2007–2009 환상·그로테스크 계열의
개별 비평 심화(오형엽) → 2010 서정시학 특집의 <b>회고·정리형 메타담론 집중</b> → 2013·2018 재평가(이재복·조재룡)
→ 2024 '미래파 이후'(정명교)로 이어지는 흐름을 위 도표·표에서 확인할 수 있다.</div>

<p class='lead' style='margin-top:30px'>※ 원자료: critic_summary.csv · concordance_미래파.csv · movement_terms.csv · cooccurrence_미래파.csv (같은 폴더, Excel 호환 UTF-8)</p>
<script>{JS}</script></body></html>"""

with open(os.path.join(OUT, "리포트.html"), "w", encoding="utf-8") as f:
    f.write(doc_html)

print("OK")
print("named texts:", len(named), "/", len(docs))
print("movement terms:", dict(all_mv.most_common(12)))
print("top cooccur:", dict(glob_cooc.most_common(12)))
print("interp totals:", sum((d["interp"] for d in docs), Counter()))
