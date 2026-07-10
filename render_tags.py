# -*- coding: utf-8 -*-
"""미래파 폴더의 태깅된 TEI/XML을 원문 위에 색상으로 표시하는 단일 HTML 뷰어 생성."""
import os, glob, html, xml.etree.ElementTree as ET
from collections import Counter, OrderedDict

NS = "{http://www.tei-c.org/ns/1.0}"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "미래파")
OUT = os.path.join(SRC, "태깅_시각화.html")

# 인라인 태그 → (한글 라벨, css 클래스)
INLINE = {
    "persName": ("인물", "t-pers"),
    "term":     ("개념/사조", "t-term"),
    "title":    ("작품/저작", "t-title"),
    "orgName":  ("기관/매체", "t-org"),
    "date":     ("연대", "t-date"),
    "quote":    ("인용", "t-quote"),
    "interp":   ("해석/평가", "t-interp"),
    "note":     ("주석", "t-note"),
    "ref":      ("참조", "t-ref"),
}

def ln(tag):  # local name
    return tag.split("}", 1)[-1] if "}" in tag else tag

def esc(s):
    return html.escape(s or "")

def attrs_str(el):
    out = []
    for k, v in el.attrib.items():
        out.append(f"{ln(k)}={v}")
    return " · ".join(out)

def render_inline(el):
    """el 의 내용(text + 자식 + tail)을 HTML 문자열로."""
    buf = [esc(el.text)]
    for ch in el:
        buf.append(render_element(ch))
        buf.append(esc(ch.tail))
    return "".join(buf)

def render_element(el):
    name = ln(el.tag)
    if name == "lb":
        return "<br>"
    if name in ("l",):              # 운문 한 행
        return f'<span class="vline">{render_inline(el)}</span><br>'
    if name in ("lg",):             # 운문 연
        return f'<span class="stanza">{render_inline(el)}</span>'
    inner = render_inline(el)
    if name in INLINE:
        label, cls = INLINE[name]
        title = f"{label}"
        a = attrs_str(el)
        if a:
            title += " | " + a
        if name == "interp":
            val = el.get("value", "")
            cls += " iv-" + esc(val)
        if name == "note":
            return f'<sup class="t-note" title="{esc(title)}">[{inner or "주"}]</sup>'
        return f'<span class="tag {cls}" title="{esc(title)}" data-tag="{name}">{inner}</span>'
    # 알 수 없는 인라인 요소는 내용만 통과
    return inner

def count_tags(body, c):
    for el in body.iter():
        name = ln(el.tag)
        if name in INLINE:
            c[name] += 1
            if name == "interp":
                c["interp:" + el.get("value", "?")] += 1

def render_block(el, depth, out):
    name = ln(el.tag)
    if name == "div":
        h = el.find(NS + "head")
        if h is not None:
            lvl = min(depth + 2, 6)
            out.append(f"<h{lvl} class='sec'>{render_inline(h)}</h{lvl}>")
        for ch in el:
            if ln(ch.tag) == "head":
                continue
            render_block(ch, depth + 1, out)
    elif name == "p":
        # p 안의 s 들을 한 문단으로
        parts = [esc(el.text)]
        for ch in el:
            if ln(ch.tag) == "s":
                parts.append(render_inline(ch) + " ")
            else:
                parts.append(render_element(ch))
            parts.append(esc(ch.tail))
        out.append("<p>" + "".join(parts) + "</p>")
    elif name == "list":
        out.append("<ul>")
        for it in el.findall(NS + "item"):
            out.append("<li>" + render_inline(it) + "</li>")
        out.append("</ul>")
    elif name == "head":
        pass
    else:
        out.append("<p>" + render_inline(el) + "</p>")

def parse_meta(fname):
    base = fname[:-4] if fname.lower().endswith(".xml") else fname
    if base.endswith("_v2"):
        base = base[:-3]
    parts = base.split("_")
    author = parts[0] if parts else base
    year = ""
    journal = ""
    for p in parts:
        if p.isdigit() and len(p) == 4:
            year = p
    if len(parts) >= 3:
        journal = parts[-2] if parts[-1].isdigit() else parts[-1]
    return author, journal, year

CSS = """
:root{font-family:'Malgun Gothic','맑은 고딕',system-ui,sans-serif;}
*{box-sizing:border-box;}
body{margin:0;display:flex;height:100vh;color:#1f2937;background:#fff;}
#side{width:300px;flex:none;border-right:1px solid #e5e7eb;overflow:auto;background:#f9fafb;padding:12px;}
#side h1{font-size:15px;margin:4px 0 12px;}
.navbtn{display:block;width:100%;text-align:left;border:none;background:none;padding:8px 10px;border-radius:8px;cursor:pointer;font-size:12.5px;line-height:1.45;color:#374151;}
.navbtn:hover{background:#eef2ff;}
.navbtn.active{background:#4f46e5;color:#fff;}
.navbtn small{display:block;opacity:.7;font-size:11px;margin-top:2px;}
#main{flex:1;overflow:auto;padding:28px 40px;}
.panel{display:none;max-width:860px;margin:0 auto;}
.panel.active{display:block;}
.panel h2.title{font-size:22px;margin:0 0 4px;}
.meta{color:#6b7280;font-size:13px;margin-bottom:16px;}
h3.sec,h4.sec,h5.sec{margin:26px 0 10px;padding-bottom:4px;border-bottom:1px solid #eee;}
p{line-height:2.05;font-size:15.5px;margin:0 0 14px;text-align:justify;}
.stanza{display:block;margin:6px 0;padding-left:14px;border-left:2px solid #fdba74;}
.vline{display:inline;}
/* 태그 색상 */
.tag{border-radius:3px;padding:0 1px;}
.t-pers{background:#dbeafe;box-shadow:inset 0 -2px 0 #60a5fa;}
.t-term{background:#dcfce7;box-shadow:inset 0 -2px 0 #4ade80;}
.t-title{background:#ede9fe;box-shadow:inset 0 -2px 0 #a78bfa;}
.t-org{background:#ccfbf1;box-shadow:inset 0 -2px 0 #2dd4bf;}
.t-date{background:#f3f4f6;box-shadow:inset 0 -2px 0 #9ca3af;}
.t-quote{background:#fff7ed;font-style:italic;box-shadow:inset 2px 0 0 #fb923c;padding:0 3px;}
.t-ref{text-decoration:underline dotted #9ca3af;}
.t-interp{box-shadow:inset 0 -3px 0 #d1d5db;}
.iv-affirmative{box-shadow:inset 0 -3px 0 #34d399;background:#ecfdf5;}
.iv-neutral{box-shadow:inset 0 -3px 0 #9ca3af;background:#f9fafb;}
.iv-critical{box-shadow:inset 0 -3px 0 #f87171;background:#fef2f2;}
sup.t-note{color:#9ca3af;font-size:10px;cursor:help;}
/* 범례 + 통계 */
.legend{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 18px;}
.legend span{font-size:12px;padding:2px 8px;border-radius:20px;}
.stats{border-collapse:collapse;font-size:12.5px;margin:0 0 22px;}
.stats td,.stats th{border:1px solid #e5e7eb;padding:4px 10px;text-align:center;}
.stats th{background:#f3f4f6;}
.toolbar{position:sticky;top:0;background:#fff;padding:8px 0 14px;z-index:5;border-bottom:1px solid #eee;margin-bottom:18px;}
.toolbar label{font-size:12.5px;margin-right:14px;cursor:pointer;user-select:none;}
.hide-tags .tag{background:none!important;box-shadow:none!important;font-style:normal!important;padding:0!important;}
.hide-tags sup.t-note{display:none;}
"""

JS = """
document.querySelectorAll('.navbtn').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.navbtn').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  document.getElementById(b.dataset.t).classList.add('active');
  document.getElementById('main').scrollTop=0;
});
const tg=document.getElementById('toggle');
tg.onchange=()=>document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('hide-tags',!tg.checked));
"""

def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.xml")))
    nav, panels = [], []
    grand = Counter()
    for i, fp in enumerate(files):
        fname = os.path.basename(fp)
        author, journal, year = parse_meta(fname)
        try:
            tree = ET.parse(fp)
        except Exception as e:
            panels.append(f"<section class='panel' id='p{i}'><h2 class='title'>{esc(fname)}</h2>"
                          f"<p style='color:#b91c1c'>파싱 오류: {esc(str(e))}</p></section>")
            nav.append(f"<button class='navbtn' data-t='p{i}'>{esc(author)} <small>{esc(fname)}</small></button>")
            continue
        root = tree.getroot()
        title_el = root.find(f"{NS}teiHeader/{NS}fileDesc/{NS}titleStmt/{NS}title")
        title = title_el.text if title_el is not None else fname
        body = root.find(f"{NS}text/{NS}body")
        c = Counter()
        if body is not None:
            count_tags(body, c)
        grand.update({k: v for k, v in c.items() if ":" not in k})

        out = []
        for el in (body if body is not None else []):
            render_block(el, 0, out)
        # back(주석) 도 있으면 추가
        back = root.find(f"{NS}text/{NS}back")
        if back is not None:
            out.append("<h3 class='sec'>[주석/뒷부분]</h3>")
            for el in back:
                render_block(el, 0, out)

        # 통계표
        order = ["persName", "term", "title", "quote", "interp", "orgName", "date", "note", "ref"]
        cells = "".join(
            f"<td>{c.get(k,0)}</td>" for k in order)
        heads = "".join(f"<th>{INLINE.get(k,(k,))[0]}</th>" for k in order)
        iv = (f"<div class='meta'>해석 태도 ▸ 긍정 {c.get('interp:affirmative',0)} · "
              f"중립 {c.get('interp:neutral',0)} · 비판 {c.get('interp:critical',0)}</div>")
        stats = f"<table class='stats'><tr>{heads}</tr><tr>{cells}</tr></table>{iv}"

        legend = ("<div class='legend'>"
                  "<span class='t-pers'>인물</span>"
                  "<span class='t-term'>개념/사조</span>"
                  "<span class='t-title'>작품/저작</span>"
                  "<span class='t-org'>기관/매체</span>"
                  "<span class='t-date'>연대</span>"
                  "<span class='t-quote'>인용</span>"
                  "<span class='iv-affirmative'>해석:긍정</span>"
                  "<span class='iv-neutral'>해석:중립</span>"
                  "<span class='iv-critical'>해석:비판</span>"
                  "<sup class='t-note' style='font-size:13px'>[주]</sup>"
                  "</div>")

        toolbar = ("<div class='toolbar'>"
                   "<label><input type='checkbox' id='toggle' checked> 태그 색상 표시</label>"
                   "</div>")

        panel = (f"<section class='panel{' active' if i==0 else ''}' id='p{i}'>"
                 f"<h2 class='title'>{esc(title)}</h2>"
                 f"<div class='meta'>{esc(author)} · {esc(journal)} · {esc(year)} &nbsp;|&nbsp; {esc(fname)}</div>"
                 f"{toolbar}{legend}{stats}"
                 + "".join(out) + "</section>")
        panels.append(panel)
        nav.append(f"<button class='navbtn{' active' if i==0 else ''}' data-t='p{i}'>"
                   f"{esc(author)} <small>{esc(title)[:40]}</small></button>")

    doc = (f"<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
           f"<title>미래파 비평 태깅 시각화</title><style>{CSS}</style></head><body>"
           f"<nav id='side'><h1>📑 미래파 비평 태깅<br><small style='font-weight:400;color:#6b7280'>"
           f"{len(files)}편 · 클릭하여 전환</small></h1>" + "".join(nav) + "</nav>"
           f"<div id='main'>" + "".join(panels) + "</div>"
           f"<script>{JS}</script></body></html>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print("OK ->", OUT)
    print("files:", len(files))
    print("grand totals:", dict(grand))

if __name__ == "__main__":
    main()
