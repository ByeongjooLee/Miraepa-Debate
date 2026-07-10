# -*- coding: utf-8 -*-
"""연도별 텍스트 밀도 + 미래파 호명 강도 → 시기구분을 데이터로 점검."""
import os, glob, csv, xml.etree.ElementTree as ET
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

byyear = defaultdict(lambda: {"n": 0, "mr": 0, "name": 0, "auth": []})
for fp in sorted(glob.glob(os.path.join(SRC, "*.xml"))):
    fn = os.path.basename(fp); a, y = meta(fn)
    if y == 0: continue
    try: body = ET.parse(fp).getroot().find(f"{NS}text/{NS}body")
    except Exception: continue
    if body is None: continue
    t = txt(body); m = t.count("미래파")
    d = byyear[y]; d["n"] += 1; d["mr"] += m; d["auth"].append(a)
    if m >= 5: d["name"] += 1

ys = range(2005, 2025)
with open(os.path.join(OUT, "per_year.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["연도", "텍스트수", "미래파언급합", "핵심명명(≥5)", "저자"])
    for y in ys:
        d = byyear.get(y)
        if d: w.writerow([y, d["n"], d["mr"], d["name"], " ".join(d["auth"])])
        else: w.writerow([y, 0, 0, 0, ""])

# 콘솔용 ASCII 막대 (텍스트수 / 미래파언급)
print("연도  텍스트  미래파언급")
for y in ys:
    d = byyear.get(y, {"n": 0, "mr": 0})
    bar = "#" * d["n"]
    print(f"{y}  {d['n']:>2} {bar:<8} 미래파={d['mr']}")
print("\n총 텍스트:", sum(byyear[y]['n'] for y in byyear), "/ 미래파 총언급:", sum(byyear[y]['mr'] for y in byyear))
