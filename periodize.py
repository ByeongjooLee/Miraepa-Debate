# -*- coding: utf-8 -*-
"""미래파 담론 시기구분: 태깅 54편을 4단계(I~IV)로 분류 + 전체 92편 밀도 대비."""
import os, glob, csv, html, xml.etree.ElementTree as ET

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

# 단계 정의
def phase(y):
    if 2005 <= y <= 2007: return "I"
    if 2008 <= y <= 2009: return "II"
    if 2010 <= y <= 2011: return "III"
    if y == 2012:        return "X"
    if y >= 2013:        return "IV"
    return "?"
PH = {
 "I":   ("I. 발생·논쟁",     "2005–07", "참여(명명 경합: 옹호↔거부)", "#4f46e5"),
 "II":  ("II. 분기·이론화",  "2008–09", "참여+회고 공존",            "#0891b2"),
 "III": ("III. 정리·일단락", "2010–11", "회고 우세",                "#d97706"),
 "X":   ("〔침묵〕",          "2012",    "—",                        "#9ca3af"),
 "IV":  ("IV. 사후 역사화",  "2013–24", "역사화(비-담론·산발)",      "#dc2626"),
}
# 전체 92편 연도별 편수(서지목록 기준) → 커버리지 비교
BIBLIO = {2005:4,2006:11,2007:13,2008:6,2009:9,2010:14,2011:4,2012:0,
          2013:6,2014:2,2015:4,2016:4,2017:1,2018:3,2019:6,2020:1,2021:3,2022:0,2023:0,2024:1}

docs = []
for fp in sorted(glob.glob(os.path.join(SRC, "*.xml"))):
    fn = os.path.basename(fp); a, y = meta(fn)
    if y == 0: continue
    try: root = ET.parse(fp).getroot()
    except Exception: continue
    te = root.find(f"{NS}teiHeader/{NS}fileDesc/{NS}titleStmt/{NS}title")
    title = (te.text if te is not None and te.text else fn).strip()
    body = root.find(f"{NS}text/{NS}body")
    nk = txt(body).count("미래파") if body is not None else 0
    docs.append(dict(a=a, y=y, t=title, nk=nk, ph=phase(y)))

# 단계별 집계
order = ["I", "II", "III", "X", "IV"]
bycov = {}
for k in order:
    yrs = [y for y in BIBLIO if phase(y) == k]
    bib = sum(BIBLIO[y] for y in yrs)
    tag = sum(1 for d in docs if d["ph"] == k)
    bycov[k] = (tag, bib)

# CSV
with open(os.path.join(OUT, "periodization.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["단계", "시기", "저자", "연도", "미래파언급", "제목"])
    for k in order:
        for d in sorted([x for x in docs if x["ph"] == k], key=lambda x: (x["y"], x["a"])):
            w.writerow([k, PH[k][1], d["a"], d["y"], d["nk"], d["t"]])

# HTML
def rows(k):
    out = ""
    for d in sorted([x for x in docs if x["ph"] == k], key=lambda x: (x["y"], x["a"])):
        out += (f"<tr><td>{d['y']}</td><td>{html.escape(d['a'])}</td>"
                f"<td class='ti'>{html.escape(d['t'][:54])}</td>"
                f"<td style='text-align:right'>{d['nk']}</td></tr>")
    return out
CSS = """body{font-family:'Malgun Gothic',sans-serif;max-width:900px;margin:0 auto;padding:24px;color:#1f2937}
h1{font-size:21px}.sub{color:#6b7280;font-size:13px;margin-bottom:16px}
.ph{margin:18px 0 6px;padding:8px 12px;border-radius:8px;color:#fff;display:flex;justify-content:space-between;align-items:baseline}
.ph b{font-size:15px}.ph span{font-size:12px;opacity:.92}
table{border-collapse:collapse;width:100%;font-size:12.5px;margin-bottom:4px}
td,th{border:1px solid #e5e7eb;padding:4px 8px}th{background:#f8fafc}.ti{color:#475569}
.cov{font-size:11.5px;color:#6b7280;margin:2px 0 10px}.bar{display:inline-block;height:9px;border-radius:2px;vertical-align:middle}"""
body = f"<h1>미래파 담론 시기구분</h1><p class='sub'>태깅 {len(docs)}편을 4단계로 분류 · 미래파언급=본문 출현수 · 커버리지=태깅/전체92편</p>"
for k in order:
    nm, per, mode, col = PH[k]
    tag, bib = bycov[k]
    body += (f"<div class='ph' style='background:{col}'><b>{nm} <span>({per})</span></b>"
             f"<span>모드: {mode}</span></div>")
    if k == "X":
        body += "<div class='cov'>2012년 = 0편(담론 휴지). 단계 III와 IV를 가르는 자연 절단점.</div>"; continue
    pct = int(tag / bib * 120) if bib else 0
    body += (f"<div class='cov'>태깅 커버리지 <b>{tag}/{bib}편</b> "
             f"<span class='bar' style='width:{pct}px;background:{col}'></span></div>")
    body += f"<table><tr><th>연도</th><th>저자</th><th>제목</th><th>미래파</th></tr>{rows(k)}</table>"
open(os.path.join(OUT, "periodization.html"), "w", encoding="utf-8").write(
    f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>{body}")

print("docs", len(docs))
for k in order:
    print(k, PH[k][1], "tagged/biblio=", bycov[k])
