# -*- coding: utf-8 -*-
"""ocr_audit.py — 정제 이전 OCR 노이즈 감사(진단). 무엇을·어디를 고칠지 먼저 파악."""
import os, glob, re, xml.etree.ElementTree as ET
from collections import Counter

NS = "{http://www.tei-c.org/ns/1.0}"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mirea_results")
DOCX = os.path.join(os.path.dirname(HERE), "생성형 ai를활용한 xml테그", "선행평론", "선행평론")
def txt(el): return "".join(el.itertext())

CID = re.compile(r"\(cid:\d+\)")
LATIN = re.compile(r"[A-Za-z]")
def is_h(c): return "가" <= c <= "힣"
def is_hanja(c): return "㐀" <= c <= "鿿"
PUNCT = set(" \n\t.,!?:;'\"()[]{}「」『』〈〉《》·…―—-~%°’‘“”、。，？！／·∼（）；　")

rows = []
tot_cid = 0
for fp in sorted(glob.glob(os.path.join(SRC, "*.xml"))):
    fn = os.path.basename(fp)
    try: body = ET.parse(fp).getroot().find(f"{NS}text/{NS}body")
    except Exception: continue
    if body is None: continue
    t = txt(body); nz = sum(1 for c in t if not c.isspace()) or 1
    cid = len(CID.findall(t)); tot_cid += cid
    # 잡기호(한글/한자/라틴/숫자/표준부호 아님) - cid 제거 후
    t2 = CID.sub("", t)
    noise = sum(1 for c in t2 if not(is_h(c) or is_hanja(c) or LATIN.match(c) or c.isdigit() or c in PUNCT))
    # 한글에 낀 라틴
    latin_intr = sum(1 for i, c in enumerate(t2) if LATIN.match(c) and
                     ((i > 0 and is_h(t2[i-1])) or (i < len(t2)-1 and is_h(t2[i+1]))))
    rows.append((fn, nz, cid, noise, latin_intr,
                 round((cid*8 + noise + latin_intr)/nz*1000, 1)))  # 종합 노이즈‰(cid 가중)

rows.sort(key=lambda r: -r[5])
out = [f"OCR 노이즈 감사 — {len(rows)}편 · CID코드 총 {tot_cid}개", ""]
out.append(f"{'노이즈‰':>7} {'CID':>5} {'잡기호':>6} {'라틴침입':>7}  파일")
for fn, nz, cid, noise, li, score in rows[:15]:
    dx = "✅docx" if glob.glob(os.path.join(DOCX, fn.split("_")[0]+"*"+".docx")) else ""
    out.append(f"{score:>7} {cid:>5} {noise:>6} {li:>7}  {fn[:46]} {dx}")
out.append("\n[정제 대상 분류]")
cid_files = [r[0] for r in rows if r[2] > 5]
out.append(f"· CID 깨짐(>5): {len(cid_files)}편 — {', '.join(f[:14] for f in cid_files)}")
hi = [r for r in rows if r[5] > 12 and r[2] <= 5]
out.append(f"· 일반 고노이즈(>12‰, CID제외): {len(hi)}편 — {', '.join(r[0][:14] for r in hi)}")
open("_ocr_audit.txt", "w", encoding="utf-8").write("\n".join(out))
print("OK · CID총", tot_cid, "· 상위노이즈", rows[0][0][:20], rows[0][5])
