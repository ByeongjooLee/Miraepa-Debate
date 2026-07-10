# -*- coding: utf-8 -*-
"""OCR 노이즈 추정 (참조 없는 프록시). 디지털 정상본 vs 스캔OCR본 비교."""
import os, glob, csv, re, unicodedata, xml.etree.ElementTree as ET

NS = "{http://www.tei-c.org/ns/1.0}"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mirea_results")
OUT = os.path.join(HERE, "미래파_분석_확장")
def txt(el): return "".join(el.itertext())

# PDF_처리분류.md 기준 분류
CLEAN = ["고봉준_감각의 난장","권온_2000년대 시단의 한 풍경","김진희, 김문주, 조강석",
 "류신_무진장한 자유","신형철_스키조와 아나키","오형엽_마녀적 무의식","오형엽_평면",
 "오형엽_환상과 실재","오형엽_환상과 주이상스","이경수_우리는 무엇을 뒤섞고",
 "이장욱_꽃들은 세상을 버리고","이재복_한국 현대시는 진화","이형권_순환의 시간",
 "정명교_미래파 이후","조재룡_2000년대의, 시","함돈균_2000년대 서정시의 한 행방"]
CID = ["고명철_다시 묻는다","고봉준_이것은 자아의 시","장석주_한 무리의 늑대"]

def grp(fn):
    if any(fn.startswith(c) for c in CLEAN): return "정상(digital)"
    if any(fn.startswith(c) for c in CID):   return "CID폰트"
    return "스캔OCR"

# 문자 분류
def is_hangul(c): return '가' <= c <= '힣'
def is_jamo(c):   return 'ᄀ' <= c <= 'ᇿ' or '㄰' <= c <= '㆏'
def is_hanja(c):  return '㐀' <= c <= '鿿'
def is_latin(c):  return ('a' <= c <= 'z') or ('A' <= c <= 'Z')
PUNCT = set(' \n\t.,!?:;\'\"()[]{}「」『』〈〉《》·…―—-~%°’‘“”、。，？！／／·∼')
def is_punct(c):  return c in PUNCT or c.isdigit()

def analyze(text):
    n = len(text); nz = sum(1 for c in text if not c.isspace())
    if nz == 0: return None
    hang=jamo=hanja=latin=noise=lat_intr=0
    chars = list(text)
    for i, c in enumerate(chars):
        if c.isspace(): continue
        if is_hangul(c): hang += 1
        elif is_jamo(c): jamo += 1; noise += 1      # 고립 자모 = 노이즈
        elif is_hanja(c): hanja += 1
        elif is_latin(c):
            latin += 1
            prv = chars[i-1] if i>0 else ' '
            nxt = chars[i+1] if i<len(chars)-1 else ' '
            if is_hangul(prv) or is_hangul(nxt): lat_intr += 1   # 한글에 낀 라틴
        elif is_punct(c): pass
        elif c.isdigit(): pass
        else: noise += 1                              # 잡기호(卜 三 ■ ＞ 등)
    # 깨진 띄어쓰기 프록시: 1글자 한글 토큰 비율
    toks = [t for t in re.split(r'\s+', text) if t]
    one = sum(1 for t in toks if len(t)==1 and is_hangul(t))
    return dict(nz=nz, hang=hang, hanja=hanja, latin=latin, noise=noise,
                lat_intr=lat_intr, toks=len(toks), one=one)

rows=[]; agg={}
for fp in sorted(glob.glob(os.path.join(SRC,"*.xml"))):
    fn=os.path.basename(fp)
    try: body=ET.parse(fp).getroot().find(f"{NS}text/{NS}body")
    except Exception: continue
    if body is None: continue
    a=analyze(txt(body))
    if not a: continue
    g=grp(fn)
    noise_rate=a["noise"]/a["nz"]*1000          # 잡기호 ‰(천분율)
    lat_intr_rate=a["lat_intr"]/a["nz"]*1000
    one_ratio=a["one"]/a["toks"]*100
    rows.append((g, fn[:40], a["nz"], round(noise_rate,2), round(lat_intr_rate,2),
                 round(one_ratio,1), a["hanja"], a["latin"]))
    agg.setdefault(g,[]).append((noise_rate,lat_intr_rate,one_ratio,a["nz"]))

# CSV
with open(os.path.join(OUT,"ocr_quality.csv"),"w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["구분","파일","글자수","잡기호‰","라틴침입‰","1글자토큰%","한자수","라틴수"])
    for r in sorted(rows,key=lambda x:-x[3]): w.writerow(r)

print("=== 그룹 평균 (글자수 가중) ===")
print(f"{'구분':<16}{'편수':>4}{'잡기호‰':>9}{'라틴침입‰':>10}{'1글자토큰%':>11}")
for g in ["정상(digital)","CID폰트","스캔OCR"]:
    L=agg.get(g,[])
    if not L: continue
    tw=sum(x[3] for x in L)
    nr=sum(x[0]*x[3] for x in L)/tw; li=sum(x[1]*x[3] for x in L)/tw; on=sum(x[2]*x[3] for x in L)/tw
    print(f"{g:<16}{len(L):>4}{nr:>9.2f}{li:>10.2f}{on:>11.1f}")
print("\n=== 스캔OCR 최악 8편 (잡기호‰) ===")
for r in sorted([x for x in rows if x[0]=='스캔OCR'],key=lambda x:-x[3])[:8]:
    print(f"  {r[3]:>6.1f}‰ 라틴침입{r[4]:>5.1f}‰ 1글자{r[5]:>4.1f}%  {r[1]}")
