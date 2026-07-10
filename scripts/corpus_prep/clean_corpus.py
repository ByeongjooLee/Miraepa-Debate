# -*- coding: utf-8 -*-
"""
clean_corpus.py — OCR 선별 정제 (원본 보존 + 정제본 + 변경로그)

정책(보수적·투명):
  · (cid:NNNN) 한자 깨짐코드 제거
  · '확인된 OCR 쓰레기 문자'만 제거(정상 기호 é/«»/·/‑ 등은 보존)
  · 고립 한글 자모(OCR 파편) 제거
  · 태그 구조는 건드리지 않음(각 요소의 .text/.tail만 정제)
  · 문자치환형 오류(웅→응 등)와 깨진 띄어쓰기는 *자동수정 안 함* → 재-OCR 후보로 보고만
"""
import os, glob, re, shutil
import xml.etree.ElementTree as ET
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mirea_results")
DST = os.path.join(HERE, "mirea_clean")
NS = "http://www.tei-c.org/ns/1.0"
ET.register_namespace("", NS)
ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")

CID = re.compile(r"\(cid:\d+\)")
# 확인된 OCR 쓰레기(인벤토리 근거). 정상 기호는 제외.
GARBAGE = set("�■^►▼◀▶◎♦▲◇□〓㈱〒◈☞★☆♠♣▷◁▬")
def is_jamo(c): return "ᄀ" <= c <= "ᇿ" or "㄰" <= c <= "㆏"

removed = Counter()
def clean(s):
    if not s: return s
    s2 = CID.sub("", s)
    out = []
    for c in s2:
        if c in GARBAGE or is_jamo(c):
            removed[c] += 1; continue
        out.append(c)
    # cid 제거분 집계
    return "".join(out)

def walk(el):
    el.text = clean(el.text); el.tail = clean(el.tail)
    for ch in el: walk(ch)

os.makedirs(DST, exist_ok=True)
log = []
tot_cid = 0
for fp in sorted(glob.glob(os.path.join(SRC, "*.xml"))):
    fn = os.path.basename(fp)
    raw = open(fp, encoding="utf-8").read()
    ncid = len(CID.findall(raw))
    tot_cid += ncid
    before = len(removed)
    tree = ET.parse(fp); walk(tree.getroot())
    tree.write(os.path.join(DST, fn), encoding="utf-8", xml_declaration=True)
    # 파일별 제거량(근사)
    if ncid or sum(removed.values()):
        pass
    log.append((fn, ncid))

# labels.json 등은 복사 안 함(분석은 xml만)
rep = [f"정제 완료 → {DST}", f"CID코드 제거 총 {tot_cid}개",
       f"쓰레기 문자 제거 종류 {len(removed)}: " +
       ", ".join(f"{c!r}×{n}" for c, n in removed.most_common(20)),
       "", "※ 문자치환(웅→응)·깨진 띄어쓰기는 자동수정 안 함(재-OCR 후보):",
       "   전해수'16 · 조해옥'16 · 조대한'21 · 고명철'08 · 오형엽(환상과실재)'08"]
open(os.path.join(HERE, "_clean_log.txt"), "w", encoding="utf-8").write("\n".join(rep))
print("OK cid=%d, garbage_kinds=%d, garbage_tokens=%d" % (tot_cid, len(removed), sum(removed.values())))
