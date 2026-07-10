# -*- coding: utf-8 -*-
"""'미래파 논쟁 텍스트 xml'의 시기별 XML을 시기별 편집가능 HTML로 생성 → '미래파 논쟁 html'.
   기존 build_editor.py의 렌더러(R)·CSS·JS·헬퍼를 재사용."""
import os, glob, json, base64
import xml.etree.ElementTree as ET
from collections import Counter
import build_editor as BE   # R, CSS, JS, parse_meta, INLINE, ln, esc, NS 재사용

HERE = os.path.dirname(os.path.abspath(__file__))
PSRC = os.path.join(HERE, "미래파 논쟁 텍스트 xml")
POUT = os.path.join(HERE, "미래파 논쟁 html")
PERIODS = ["1_발생기(2005-2007)", "2_이론화기(2008-2009)",
           "3_정리기(2010-2011)", "4_사후역사화(2013-2024)"]
ORDER = ["persName", "term", "title", "quote", "interp", "orgName", "date", "note", "ref"]


def build_one(files, out_path, page_title):
    nav, panels = [], []
    raw_map, name_map = {}, {}
    for i, fp in enumerate(files):
        fname = os.path.basename(fp)
        author, journal, year, base = BE.parse_meta(fname)
        raw = open(fp, "r", encoding="utf-8").read()
        raw_map[i] = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        name_map[i] = fname
        try:
            root = ET.parse(fp).getroot()
        except Exception as e:
            panels.append(f"<section class='panel' id='p{i}'><h2 class='title'>{BE.esc(fname)}</h2>"
                          f"<p style='color:#b91c1c'>파싱 오류: {BE.esc(str(e))}</p></section>")
            nav.append(f"<button class='navbtn' data-t='p{i}'>{BE.esc(author)}<small>{BE.esc(fname)}</small></button>")
            continue
        t_el = root.find(f"{BE.NS}teiHeader/{BE.NS}fileDesc/{BE.NS}titleStmt/{BE.NS}title")
        title = t_el.text if t_el is not None else fname
        body = root.find(f"{BE.NS}text/{BE.NS}body")
        c = Counter()
        if body is not None:
            for el in body.iter():
                n = BE.ln(el.tag)
                if n in BE.INLINE:
                    c[n] += 1
                    if n == "interp":
                        c["i:" + el.get("value", "?")] += 1
        editor = "".join(BE.R(ch) for ch in (body if body is not None else []))
        heads = "".join(f"<th>{BE.INLINE[k][0]}</th>" for k in ORDER)
        cells = "".join(f"<td data-cnt='{k}'>{c.get(k,0)}</td>" for k in ORDER)
        iv = (f"<div class='meta'>해석 태도 ▸ <b data-iv>긍정 {c.get('i:affirmative',0)} · "
              f"중립 {c.get('i:neutral',0)} · 비판 {c.get('i:critical',0)}</b></div>")
        stats = f"<table class='stats'><tr>{heads}</tr><tr>{cells}</tr></table>{iv}"
        toolbar = (f"<div class='toolbar'>"
                   f"<button class='btn exp' onclick='exportXml({i})'>⬇ 수정본 XML 내보내기</button>"
                   f"<button class='btn' onclick='refreshStats()'>↻ 통계 갱신</button>"
                   f"<label><input type='checkbox' checked onchange='document.getElementById(\"ed-{i}\").classList.toggle(\"nolbl\",!this.checked)'> 태그 라벨</label>"
                   f"<label><input type='checkbox' onchange='document.getElementById(\"ed-{i}\").classList.toggle(\"bg\",this.checked)'> 배경색</label>"
                   f"<span style='color:#9ca3af;font-size:11.5px'>라벨 클릭=편집 · 본문 드래그=태그 추가</span></div>")
        panels.append(f"<section class='panel{' active' if i==0 else ''}' id='p{i}'>"
                      f"<h2 class='title'>{BE.esc(title)}</h2>"
                      f"<div class='meta'>{BE.esc(author)} · {BE.esc(journal)} · {BE.esc(year)} &nbsp;|&nbsp; {BE.esc(fname)}</div>"
                      f"{toolbar}{stats}<div class='editor' id='ed-{i}'>{editor}</div></section>")
        nav.append(f"<button class='navbtn{' active' if i==0 else ''}' data-t='p{i}'>"
                   f"{BE.esc(author)}<small>{BE.esc(title)[:38]}</small></button>")
    data = (f"<script>const RAW={json.dumps(raw_map)};"
            f"const NAMES={json.dumps(name_map, ensure_ascii=False)};</script>")
    doc = ("<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
           f"<title>{BE.esc(page_title)}</title><style>" + BE.CSS + "</style></head><body>"
           f"<nav id='side'><h1>✏️ {BE.esc(page_title)}<br><small style='font-weight:400;color:#6b7280'>"
           f"{len(files)}편 · 라벨클릭 편집 · 내보내기</small></h1>" + "".join(nav) + "</nav>"
           "<div id='main'>" + "".join(panels) + "</div>"
           "<div id='addbar'></div><div id='pop'></div>"
           + data + "<script>" + BE.JS + "</script></body></html>")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(doc)
    return len(files)


def main():
    os.makedirs(POUT, exist_ok=True)
    total = 0
    for p in PERIODS:
        files = sorted(glob.glob(os.path.join(PSRC, p, "*.xml")))
        if not files:
            continue
        n = build_one(files, os.path.join(POUT, p + ".html"), p.split("_", 1)[-1])
        total += n
        print(p, n)
    allf = sorted(glob.glob(os.path.join(PSRC, "**", "*.xml"), recursive=True))
    build_one(allf, os.path.join(POUT, "0_전체.html"), "미래파 논쟁 전체")
    print("전체", len(allf), "· 시기합", total)


if __name__ == "__main__":
    main()
