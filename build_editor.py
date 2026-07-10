# -*- coding: utf-8 -*-
"""미래파 폴더의 태깅 XML을 (1)작은 라벨로 표시하고 (2)브라우저에서 직접 수정→XML 내보내기 할 수 있는 단일 HTML 에디터 생성."""
import os, glob, json, base64, html, xml.etree.ElementTree as ET
from collections import Counter

NS = "{http://www.tei-c.org/ns/1.0}"
XMLID = "{http://www.w3.org/XML/1998/namespace}id"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "미래파")
OUT = os.path.join(SRC, "태깅_에디터.html")

INLINE = {  # 태그 → (한글, css클래스)
    "persName": ("인물", "t-pers"), "term": ("개념/사조", "t-term"),
    "title": ("작품/저작", "t-title"), "orgName": ("기관/매체", "t-org"),
    "date": ("연대", "t-date"), "quote": ("인용", "t-quote"),
    "interp": ("해석/평가", "t-interp"), "note": ("주석", "t-note"),
    "ref": ("참조", "t-ref"),
}

def ln(t): return t.split("}", 1)[-1] if "}" in t else t
def esc(s): return html.escape(s or "")
def attr_map(el):
    d = {}
    for k, v in el.attrib.items():
        d["xml:id" if k == XMLID else ln(k)] = v
    return d
def aj(el):
    return html.escape(json.dumps(attr_map(el), ensure_ascii=False), quote=True)
def tip(el):
    a = attr_map(el)
    s = ln(el.tag)
    if a:
        s += " | " + "; ".join(f"{k}={v}" for k, v in a.items())
    return html.escape(s, quote=True)

def R(el):
    """모든 TEI 요소를 data-el 을 가진 DOM 으로 (왕복 직렬화 가능)."""
    name = ln(el.tag)
    if name == "lb":
        return '<span data-el="lb" class="lb"></span><br>'
    inner = esc(el.text)
    for ch in el:
        inner += R(ch) + esc(ch.tail)
    if name in INLINE:
        label, cls = INLINE[name]
        if name == "interp":
            cls += " iv-" + esc(el.get("value", ""))
        return (f'<span class="el inl {cls}" data-el="{name}" data-attrs="{aj(el)}" '
                f'title="{tip(el)}">{inner}<span class="lbl">{name}</span></span>')
    if name == "div":
        return f'<div class="d" data-el="div" data-attrs="{aj(el)}">{inner}</div>'
    if name == "head":
        return f'<h4 class="sec" data-el="head" data-attrs="{aj(el)}">{inner}</h4>'
    if name == "p":
        return f'<p data-el="p" data-attrs="{aj(el)}">{inner}</p>'
    if name == "s":
        return f'<span class="s" data-el="s" data-attrs="{aj(el)}">{inner} </span>'
    if name == "lg":
        return f'<span class="stanza" data-el="lg" data-attrs="{aj(el)}">{inner}</span>'
    if name == "l":
        return f'<span class="vline" data-el="l" data-attrs="{aj(el)}">{inner}</span><br>'
    if name == "list":
        return f'<ul data-el="list" data-attrs="{aj(el)}">{inner}</ul>'
    if name == "item":
        return f'<li data-el="item" data-attrs="{aj(el)}">{inner}</li>'
    return inner

def parse_meta(fname):
    base = fname[:-4] if fname.lower().endswith(".xml") else fname
    if base.endswith("_v2"): base = base[:-3]
    parts = base.split("_")
    author = parts[0] if parts else base
    year = next((p for p in parts if p.isdigit() and len(p) == 4), "")
    journal = ""
    if len(parts) >= 3:
        journal = parts[-2] if parts[-1].isdigit() else parts[-1]
    return author, journal, year, base

CSS = r"""
:root{font-family:'Malgun Gothic',system-ui,sans-serif}
*{box-sizing:border-box}
body{margin:0;display:flex;height:100vh;color:#1f2937}
#side{width:290px;flex:none;border-right:1px solid #e5e7eb;overflow:auto;background:#f9fafb;padding:12px}
#side h1{font-size:14px;margin:4px 0 10px}
.navbtn{display:block;width:100%;text-align:left;border:none;background:none;padding:7px 9px;border-radius:8px;cursor:pointer;font-size:12px;line-height:1.4;color:#374151}
.navbtn:hover{background:#eef2ff}.navbtn.active{background:#4f46e5;color:#fff}
.navbtn small{display:block;opacity:.7;font-size:10.5px;margin-top:2px}
#main{flex:1;overflow:auto;padding:24px 36px}
.panel{display:none;max-width:880px;margin:0 auto}.panel.active{display:block}
.panel h2.title{font-size:21px;margin:0 0 3px}.meta{color:#6b7280;font-size:12.5px;margin-bottom:12px}
h4.sec{margin:24px 0 10px;padding-bottom:4px;border-bottom:1px solid #eee;font-size:16px}
p{line-height:2.15;font-size:15.5px;margin:0 0 14px;text-align:justify}
.stanza{display:block;margin:6px 0;padding-left:14px;border-left:2px solid #fdba74}
/* 인라인 태그: 기본은 옅은 밑줄 + 작은 라벨 */
.el.inl{border-bottom:1px solid #d1d5db;cursor:default;position:relative}
.lbl{font-size:9px;vertical-align:super;line-height:0;margin-left:1px;padding:0 2px;border-radius:3px;background:#f1f5f9;color:#64748b;cursor:pointer;user-select:none;letter-spacing:-.3px}
.lbl:hover{outline:1px solid #6366f1}
.t-pers{border-bottom-color:#60a5fa}.t-pers .lbl{color:#1d4ed8;background:#dbeafe}
.t-term{border-bottom-color:#4ade80}.t-term .lbl{color:#15803d;background:#dcfce7}
.t-title{border-bottom-color:#a78bfa}.t-title .lbl{color:#6d28d9;background:#ede9fe}
.t-org{border-bottom-color:#2dd4bf}.t-org .lbl{color:#0f766e;background:#ccfbf1}
.t-date{border-bottom-color:#9ca3af}.t-date .lbl{color:#4b5563;background:#f3f4f6}
.t-quote{border-bottom-color:#fb923c;font-style:italic}.t-quote .lbl{color:#c2410c;background:#ffedd5}
.t-interp .lbl{color:#7c3aed;background:#f3e8ff}
.t-note .lbl{color:#64748b}.t-ref .lbl{color:#64748b}
.iv-affirmative{border-bottom:2px solid #34d399}.iv-neutral{border-bottom:2px solid #9ca3af}.iv-critical{border-bottom:2px solid #f87171}
/* 배경색 모드 */
.bg .t-pers{background:#dbeafe}.bg .t-term{background:#dcfce7}.bg .t-title{background:#ede9fe}
.bg .t-org{background:#ccfbf1}.bg .t-date{background:#f3f4f6}.bg .t-quote{background:#fff7ed}
.bg .iv-affirmative{background:#ecfdf5}.bg .iv-neutral{background:#f9fafb}.bg .iv-critical{background:#fef2f2}
/* 라벨 숨김 */
.nolbl .lbl{display:none}
.toolbar{position:sticky;top:0;background:#fff;padding:8px 0 12px;z-index:5;border-bottom:1px solid #eee;margin-bottom:14px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.toolbar label{font-size:12px;cursor:pointer;user-select:none}
.btn{font-size:12px;padding:5px 11px;border:1px solid #c7d2fe;background:#eef2ff;color:#4338ca;border-radius:7px;cursor:pointer}
.btn:hover{background:#e0e7ff}
.btn.exp{border-color:#34d399;background:#ecfdf5;color:#047857}
.stats{border-collapse:collapse;font-size:12px;margin:0 0 16px}
.stats td,.stats th{border:1px solid #e5e7eb;padding:3px 9px;text-align:center}.stats th{background:#f3f4f6}
/* 선택 시 뜨는 태그 추가 바 */
#addbar{position:fixed;display:none;z-index:50;background:#111827;border-radius:9px;padding:5px;box-shadow:0 6px 20px rgba(0,0,0,.3);gap:3px}
#addbar.show{display:flex}
#addbar button{font-size:11px;border:none;background:#374151;color:#fff;padding:4px 8px;border-radius:6px;cursor:pointer}
#addbar button:hover{background:#4f46e5}
/* 속성 편집 팝오버 */
#pop{position:fixed;display:none;z-index:60;background:#fff;border:1px solid #d1d5db;border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.18);padding:12px;width:300px;font-size:12px}
#pop.show{display:block}
#pop h3{margin:0 0 8px;font-size:13px}
#pop .row{display:flex;align-items:center;gap:6px;margin:5px 0}
#pop .row span{width:64px;color:#6b7280;flex:none}
#pop select,#pop input{flex:1;font-size:12px;padding:3px 5px;border:1px solid #d1d5db;border-radius:5px}
#pop .acts{display:flex;gap:6px;margin-top:10px}
#pop .acts button{flex:1;font-size:12px;padding:6px;border-radius:6px;border:none;cursor:pointer}
.b-apply{background:#4f46e5;color:#fff}.b-del{background:#fee2e2;color:#b91c1c}.b-close{background:#f3f4f6;color:#374151}
"""

JS = r"""
const KINDS=['persName','term','title','orgName','date','quote','interp','note','ref'];
const KLABEL={persName:'인물',term:'개념/사조',title:'작품/저작',orgName:'기관/매체',date:'연대',quote:'인용',interp:'해석/평가',note:'주석',ref:'참조'};
const CLS={persName:'t-pers',term:'t-term',title:'t-title',orgName:'t-org',date:'t-date',quote:'t-quote',interp:'t-interp',note:'t-note',ref:'t-ref'};
const ROLES=['','critic','novelist','poet','playwright','essayist','translator','childrenauthor','scholar','foreigner','writer','other'];
const TTYPE=['','critic','novel','poem','play','essay','translation','children','contribution','foreign','other','journal','newspaper','coterie','publication'];
const QTYPE=['','direct','indirect','paraphrase','contribution','criticism','review','commentary'];
const QGEN=['','critic','novel','poet','play','essay','translation','children','contribution','foreign','other'];
const SPEC={
 persName:[['role','sel',ROLES],['ref','t'],['xml:id','t'],['lang','t']],
 term:[['type','t']],
 title:[['level','sel',['','m','a','j']],['type','sel',TTYPE],['ref','t'],['xml:id','t']],
 orgName:[['ref','t'],['xml:id','t']],
 date:[['when','t'],['from','t'],['to','t'],['notBefore','t'],['notAfter','t']],
 quote:[['type','sel',QTYPE],['genre','sel',QGEN],['source','t'],['ana','t']],
 interp:[['value','sel',['','affirmative','neutral','critical']],['ana','t']],
 note:[['type','t'],['target','t'],['ana','t']],
 ref:[['target','t']],
};
// ---- 탭 전환 ----
document.querySelectorAll('.navbtn').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.navbtn').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');document.getElementById(b.dataset.t).classList.add('active');
  document.getElementById('main').scrollTop=0;hidePop();hideAdd();
});
// ---- 토글 (라벨/배경) ----
function applyToggles(){
  const lbl=document.getElementById('cb-lbl').checked, bg=document.getElementById('cb-bg').checked;
  document.querySelectorAll('.editor').forEach(e=>{e.classList.toggle('nolbl',!lbl);e.classList.toggle('bg',bg);});
}
// ---- 라벨 클릭 → 속성 팝오버 ----
let curSpan=null;
document.querySelectorAll('.editor').forEach(ed=>{
  ed.addEventListener('click',e=>{
    if(e.target.classList.contains('lbl')){e.stopPropagation();openPop(e.target.parentElement,e);}
  });
});
const pop=document.getElementById('pop');
function openPop(span,ev){
  curSpan=span;const kind=span.dataset.el;let attrs={};try{attrs=JSON.parse(span.dataset.attrs||'{}')}catch(_){}
  let h='<h3>태그 편집</h3><div class="row"><span>종류</span><select id="pk">';
  KINDS.forEach(k=>h+=`<option value="${k}"${k===kind?' selected':''}>${KLABEL[k]} (${k})</option>`);
  h+='</select></div><div id="pf"></div><div class="acts">'
    +'<button class="b-apply">적용</button><button class="b-del">태그 해제</button><button class="b-close">닫기</button></div>';
  pop.innerHTML=h;
  buildFields(kind,attrs);
  pop.querySelector('#pk').onchange=e=>buildFields(e.target.value,{});
  pop.querySelector('.b-apply').onclick=applyPop;
  pop.querySelector('.b-del').onclick=()=>{unwrap(curSpan);hidePop();refreshStats();};
  pop.querySelector('.b-close').onclick=hidePop;
  pop.classList.add('show');
  const x=Math.min(ev.clientX,window.innerWidth-320),y=Math.min(ev.clientY+12,window.innerHeight-260);
  pop.style.left=x+'px';pop.style.top=y+'px';
}
function buildFields(kind,attrs){
  const f=pop.querySelector('#pf');let h='';
  (SPEC[kind]||[]).forEach(([name,type,opts])=>{
    const v=attrs[name]||'';
    if(type==='sel'){h+=`<div class="row"><span>${name}</span><select data-a="${name}">`;
      opts.forEach(o=>h+=`<option value="${o}"${o===v?' selected':''}>${o||'(없음)'}</option>`);h+='</select></div>';}
    else{h+=`<div class="row"><span>${name}</span><input data-a="${name}" value="${v.replace(/"/g,'&quot;')}"></div>`;}
  });
  f.innerHTML=h||'<div style="color:#9ca3af">속성 없음</div>';
}
function applyPop(){
  const kind=pop.querySelector('#pk').value;const attrs={};
  pop.querySelectorAll('[data-a]').forEach(i=>{if(i.value!=='')attrs[i.dataset.a]=i.value;});
  setSpan(curSpan,kind,attrs);hidePop();refreshStats();
}
function setSpan(span,kind,attrs){
  span.dataset.el=kind;span.dataset.attrs=JSON.stringify(attrs);
  let cls='el inl '+CLS[kind];if(kind==='interp'&&attrs.value)cls+=' iv-'+attrs.value;
  span.className=cls;
  let lbl=span.querySelector(':scope>.lbl');if(!lbl){lbl=document.createElement('span');lbl.className='lbl';span.appendChild(lbl);}
  lbl.textContent=kind;
  span.title=kind+(Object.keys(attrs).length?' | '+Object.entries(attrs).map(([k,v])=>k+'='+v).join('; '):'');
}
function unwrap(span){
  const lbl=span.querySelector(':scope>.lbl');if(lbl)lbl.remove();
  const p=span.parentNode;while(span.firstChild)p.insertBefore(span.firstChild,span);p.removeChild(span);
}
function hidePop(){pop.classList.remove('show');curSpan=null;}
// ---- 텍스트 선택 → 태그 추가 ----
const addbar=document.getElementById('addbar');
function hideAdd(){addbar.classList.remove('show');}
document.getElementById('main').addEventListener('mouseup',e=>{
  if(e.target.closest('#pop')||e.target.classList.contains('lbl'))return;
  setTimeout(()=>{
    const sel=getSelection();
    if(!sel.rangeCount||sel.isCollapsed){hideAdd();return;}
    const r=sel.getRangeAt(0);const ed=r.commonAncestorContainer.parentElement?.closest('.editor');
    if(!ed||sel.toString().trim()===''){hideAdd();return;}
    let h='';KINDS.forEach(k=>h+=`<button data-k="${k}">${KLABEL[k]}</button>`);
    addbar.innerHTML=h;
    addbar.querySelectorAll('button').forEach(b=>b.onmousedown=ev=>{ev.preventDefault();wrap(b.dataset.k,r);});
    const rect=r.getBoundingClientRect();
    addbar.style.left=Math.min(rect.left,window.innerWidth-420)+'px';
    addbar.style.top=(rect.top-42)+'px';addbar.classList.add('show');
  },1);
});
function wrap(kind,range){
  const span=document.createElement('span');
  span.dataset.el=kind;span.dataset.attrs='{}';span.className='el inl '+CLS[kind];
  try{range.surroundContents(span);}
  catch(err){alert('선택 영역이 다른 태그의 경계를 가로지릅니다.\n하나의 구절(태그 안쪽 또는 바깥쪽) 안에서 선택해 주세요.');hideAdd();return;}
  const lbl=document.createElement('span');lbl.className='lbl';lbl.textContent=kind;span.appendChild(lbl);
  getSelection().removeAllRanges();hideAdd();
  openPop(span,{clientX:window.innerWidth/2-150,clientY:160});refreshStats();
}
// ---- 통계 갱신 ----
function refreshStats(){
  document.querySelectorAll('.panel').forEach(p=>{
    const ed=p.querySelector('.editor');if(!ed)return;const c={};
    ed.querySelectorAll('[data-el]').forEach(s=>{const k=s.dataset.el;if(KLABEL[k])c[k]=(c[k]||0)+1;});
    p.querySelectorAll('[data-cnt]').forEach(td=>td.textContent=c[td.dataset.cnt]||0);
    let af=0,nu=0,cr=0;ed.querySelectorAll('[data-el="interp"]').forEach(s=>{const v=(JSON.parse(s.dataset.attrs||'{}')).value;if(v==='affirmative')af++;else if(v==='neutral')nu++;else if(v==='critical')cr++;});
    const iv=p.querySelector('[data-iv]');if(iv)iv.textContent=`긍정 ${af} · 중립 ${nu} · 비판 ${cr}`;
  });
}
// ---- XML 직렬화 + 내보내기 ----
function escX(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function escA(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function serEl(n){
  if(n.nodeType===3)return escX(n.nodeValue);
  if(n.nodeType!==1)return '';
  if(n.classList&&n.classList.contains('lbl'))return '';
  const name=n.dataset?n.dataset.el:undefined;
  if(!name){if(n.tagName==='BR')return '';return serCh(n);}
  if(name==='lb')return '<lb/>';
  let a='';try{const o=JSON.parse(n.dataset.attrs||'{}');for(const k in o)if(o[k]!==''&&o[k]!=null)a+=' '+k+'="'+escA(o[k])+'"';}catch(_){}
  return '<'+name+a+'>'+serCh(n)+'</'+name+'>';
}
function serCh(el){let s='';el.childNodes.forEach(n=>s+=serEl(n));return s;}
function b64utf8(b){const bin=atob(b);const u=Uint8Array.from(bin,c=>c.charCodeAt(0));return new TextDecoder('utf-8').decode(u);}
function exportXml(i){
  const ed=document.getElementById('ed-'+i);const body=serCh(ed);
  const raw=b64utf8(RAW[i]);
  const o=raw.indexOf('<body');const oEnd=raw.indexOf('>',o)+1;const c=raw.lastIndexOf('</body>');
  const out=raw.slice(0,oEnd)+'\n'+body+'\n  '+raw.slice(c);
  const blob=new Blob([out],{type:'application/xml;charset=utf-8'});
  const url=URL.createObjectURL(blob);const a=document.createElement('a');
  a.href=url;a.download=NAMES[i].replace(/\.xml$/i,'')+'_edited.xml';a.click();URL.revokeObjectURL(url);
}
document.addEventListener('scroll',hidePop,true);
"""

def main():
    files = sorted(glob.glob(os.path.join(SRC, "*.xml")))
    nav, panels = [], []
    raw_map, name_map = {}, {}
    order = ["persName", "term", "title", "quote", "interp", "orgName", "date", "note", "ref"]
    for i, fp in enumerate(files):
        fname = os.path.basename(fp)
        author, journal, year, base = parse_meta(fname)
        with open(fp, "r", encoding="utf-8") as fh:
            raw = fh.read()
        raw_map[i] = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        name_map[i] = fname
        try:
            root = ET.parse(fp).getroot()
        except Exception as e:
            panels.append(f"<section class='panel' id='p{i}'><h2 class='title'>{esc(fname)}</h2>"
                          f"<p style='color:#b91c1c'>파싱 오류: {esc(str(e))}</p></section>")
            nav.append(f"<button class='navbtn' data-t='p{i}'>{esc(author)}<small>{esc(fname)}</small></button>")
            continue
        t_el = root.find(f"{NS}teiHeader/{NS}fileDesc/{NS}titleStmt/{NS}title")
        title = t_el.text if t_el is not None else fname
        body = root.find(f"{NS}text/{NS}body")
        c = Counter()
        if body is not None:
            for el in body.iter():
                n = ln(el.tag)
                if n in INLINE:
                    c[n] += 1
                    if n == "interp":
                        c["i:" + el.get("value", "?")] += 1
        editor = "".join(R(ch) for ch in (body if body is not None else []))

        heads = "".join(f"<th>{INLINE[k][0]}</th>" for k in order)
        cells = "".join(f"<td data-cnt='{k}'>{c.get(k,0)}</td>" for k in order)
        iv = (f"<div class='meta'>해석 태도 ▸ <b data-iv>긍정 {c.get('i:affirmative',0)} · "
              f"중립 {c.get('i:neutral',0)} · 비판 {c.get('i:critical',0)}</b></div>")
        stats = f"<table class='stats'><tr>{heads}</tr><tr>{cells}</tr></table>{iv}"
        toolbar = (f"<div class='toolbar'>"
                   f"<button class='btn exp' onclick='exportXml({i})'>⬇ 수정본 XML 내보내기</button>"
                   f"<button class='btn' onclick='refreshStats()'>↻ 통계 갱신</button>"
                   f"<label><input type='checkbox' checked onchange='document.getElementById(\"ed-{i}\").classList.toggle(\"nolbl\",!this.checked)'> 태그 라벨</label>"
                   f"<label><input type='checkbox' onchange='document.getElementById(\"ed-{i}\").classList.toggle(\"bg\",this.checked)'> 배경색</label>"
                   f"<span style='color:#9ca3af;font-size:11.5px'>라벨 클릭=편집 · 본문 드래그=태그 추가</span></div>")
        panel = (f"<section class='panel{' active' if i==0 else ''}' id='p{i}'>"
                 f"<h2 class='title'>{esc(title)}</h2>"
                 f"<div class='meta'>{esc(author)} · {esc(journal)} · {esc(year)} &nbsp;|&nbsp; {esc(fname)}</div>"
                 f"{toolbar}{stats}<div class='editor' id='ed-{i}'>{editor}</div></section>")
        panels.append(panel)
        nav.append(f"<button class='navbtn{' active' if i==0 else ''}' data-t='p{i}'>"
                   f"{esc(author)}<small>{esc(title)[:38]}</small></button>")

    data = (f"<script>const RAW={json.dumps(raw_map)};"
            f"const NAMES={json.dumps(name_map, ensure_ascii=False)};</script>")
    doc = ("<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
           "<title>미래파 태깅 에디터</title><style>" + CSS + "</style></head><body>"
           "<nav id='side'><h1>✏️ 미래파 태깅 에디터<br><small style='font-weight:400;color:#6b7280'>"
           f"{len(files)}편 · 라벨클릭 편집 · 내보내기</small></h1>" + "".join(nav) + "</nav>"
           "<div id='main'>" + "".join(panels) + "</div>"
           "<div id='addbar'></div><div id='pop'></div>"
           + data + "<script>" + JS + "</script></body></html>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print("OK ->", OUT)
    print("files:", len(files))

if __name__ == "__main__":
    main()
