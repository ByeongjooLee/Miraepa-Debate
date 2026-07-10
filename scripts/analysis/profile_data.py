# -*- coding: utf-8 -*-
"""미래파 담론 분석 설계를 위한 데이터 프로파일링."""
import os, glob, re, xml.etree.ElementTree as ET
from collections import Counter, defaultdict

NS = "{http://www.tei-c.org/ns/1.0}"
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "미래파")
def ln(t): return t.split("}", 1)[-1] if "}" in t else t

def text_of(el):
    return "".join(el.itertext())

def parse_meta(fname):
    base = fname[:-4]
    if base.endswith("_v2"): base = base[:-3]
    parts = base.split("_")
    year = next((p for p in parts if p.isdigit() and len(p) == 4), "?")
    return parts[0], year

KEY = "미래파"
files = sorted(glob.glob(os.path.join(SRC, "*.xml")))
print(f"총 {len(files)}개 파일\n" + "=" * 70)

all_term_types = Counter()
all_interp_vals = Counter()
term_texts_with_key = Counter()

print(f"\n[파일별 개요]  (미래파 관련: raw=원문출현, term=term태그내, interp_near=같은 문장내 interp수)")
print(f"{'저자':<8}{'연도':<6}{'전체term':>8}{'전체interp':>10}{'미래파raw':>9}{'미래파term':>10}")
for fp in files:
    fn = os.path.basename(fp)
    author, year = parse_meta(fn)
    root = ET.parse(fp).getroot()
    body = root.find(f"{NS}text/{NS}body")
    raw = text_of(body) if body is not None else ""
    n_raw = raw.count(KEY)
    n_term_total = 0
    n_term_key = 0
    n_interp = 0
    for el in body.iter():
        n = ln(el.tag)
        if n == "term":
            n_term_total += 1
            tt = el.get("type", "")
            all_term_types[tt] += 1
            t = (el.text or "").strip()
            if KEY in t:
                n_term_key += 1
                term_texts_with_key[t] += 1
        elif n == "interp":
            n_interp += 1
            all_interp_vals[el.get("value", "?")] += 1
    print(f"{author:<8}{year:<6}{n_term_total:>8}{n_interp:>10}{n_raw:>9}{n_term_key:>10}")

print("\n" + "=" * 70)
print("[term type 분포]", dict(all_term_types))
print("[interp value 분포]", dict(all_interp_vals))
print("\n[미래파를 포함해 term으로 태깅된 표현들]")
for t, c in term_texts_with_key.most_common():
    print(f"  {c:>3}  {t}")

# interp 중 미래파를 직접 포함하는 것 샘플
print("\n" + "=" * 70)
print("[interp 태그 중 본문에 '미래파' 포함하는 사례 (value / ana / 텍스트앞 60자)]")
cnt = 0
for fp in files:
    author, year = parse_meta(os.path.basename(fp))
    root = ET.parse(fp).getroot()
    body = root.find(f"{NS}text/{NS}body")
    for el in body.iter():
        if ln(el.tag) == "interp":
            txt = text_of(el)
            if KEY in txt:
                cnt += 1
                if cnt <= 20:
                    print(f"  [{author} {year}] {el.get('value','?')} / ana={el.get('ana','')} :: {txt[:60].strip()}")
print(f"  ... 총 {cnt}건")

# ana 속성 값 분포
print("\n[interp의 ana 속성 값 분포]")
ana_c = Counter()
for fp in files:
    root = ET.parse(fp).getroot()
    for el in root.iter():
        if ln(el.tag) == "interp":
            ana_c[el.get("ana", "(없음)")] += 1
for a, c in ana_c.most_common(30):
    print(f"  {c:>4}  {a}")
