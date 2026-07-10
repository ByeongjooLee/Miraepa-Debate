# -*- coding: utf-8 -*-
"""
analyses.py — 미래파 분석 함수 (안전장치 내장)

내장한 비판적 안전장치:
  · keyness: 내부 시기 비교 · min_freq · 단일자 필터 · 문서빈도(분산) 병기 · 셀 신뢰성 flag · 저빈도 ⚠
  · 담화 운율: 인용(<quote>) 제외 버전 병기(표적 오염 진단) · KWIC 표본 · N 병기
  · 명명 분산: 만자당 정규화 · 문서빈도 · 핵심명명/미언급 비율
소표본이라 LL은 절대값보다 '상대 순위'로 해석한다(gigyo 관례 준수).
"""
from __future__ import annotations
import math
from collections import Counter
from . import config as C


def log_likelihood(a: int, b: int, c: int, d: int) -> float:
    """Dunning LL. a,b=대상/참조 빈도, c,d=대상/참조 크기."""
    if a == 0 and b == 0: return 0.0
    total = c + d
    if total == 0: return 0.0
    E1 = c * (a + b) / total; E2 = d * (a + b) / total
    ll = 0.0
    if a > 0 and E1 > 0: ll += a * math.log(a / E1)
    if b > 0 and E2 > 0: ll += b * math.log(b / E2)
    return 2 * ll


def keyness_by_period(corpus, min_freq=None, top_n=None):
    """시기별 핵심어: 해당 시기 vs 나머지 시기(keyness)."""
    min_freq = min_freq or C.MIN_FREQ_KEYWORD
    top_n = top_n or C.TOP_N_KEYWORDS
    stop = set(C.STOP_WORDS)
    periods = corpus.periods()
    result = {}
    for p in periods:
        target = corpus.period_tokens(p)
        tc, tsize = Counter(target), len(target)
        others = []
        for q in periods:
            if q != p: others.extend(corpus.period_tokens(q))
        oc, osize = Counter(others), len(others)
        pdocs = corpus.period_docs(p)
        scores = []
        for w, f in tc.items():
            if f < min_freq or w in stop: continue
            of = oc.get(w, 0)
            if (f / tsize if tsize else 0) <= (of / osize if osize else 0): continue
            dfreq = sum(1 for d in pdocs if w in d.tokens)
            scores.append({"word": w, "ll": round(log_likelihood(f, of, tsize, osize), 2),
                           "freq": f, "docs": f"{dfreq}/{len(pdocs)}",
                           "flag": "⚠저빈도" if f <= C.LOWFREQ_FLAG else ""})
        scores.sort(key=lambda x: x["ll"], reverse=True)
        result[p] = {"n_docs": len(pdocs), "n_tokens": tsize,
                     "reliable": tsize >= C.MIN_CELL_TOKENS,
                     "keywords": scores[:top_n]}
    return result


def discourse_prosody(corpus, target=None):
    """'미래파' 문장의 담화 운율 — 전체 vs 인용제외 병기(표적 오염 진단)."""
    target = target or C.TARGET
    sents_by_p = corpus.sents_with(target, by_period=True)
    def idx(pp, nn): return round((pp - nn) / (pp + nn), 2) if (pp + nn) else 0.0
    result = {}
    for p in C.PERIOD_ORDER:
        ss = sents_by_p.get(p, [])
        if not ss: continue
        pf = nf = pnq = nnq = 0
        quoted = Counter(); kwic = []
        for s in ss:
            full, nq = s["text"], s["text_nq"]
            hpf = [w for w in C.POS_EVAL if w in full]; hnf = [w for w in C.NEG_EVAL if w in full]
            hpq = [w for w in C.POS_EVAL if w in nq];   hnq = [w for w in C.NEG_EVAL if w in nq]
            pf += len(hpf); nf += len(hnf); pnq += len(hpq); nnq += len(hnq)
            only_q = (set(hpf) - set(hpq)) | (set(hnf) - set(hnq))   # 인용에서만 등장
            for w in only_q: quoted[w] += 1
            if (hpf or hnf) and len(kwic) < 5:
                kwic.append({"author": s["author"], "pos": hpf, "neg": hnf,
                             "인용에서": sorted(only_q), "text": full[:95].strip()})
        result[p] = {"n_sents": len(ss),
                     "전체": {"pos": pf, "neg": nf, "index": idx(pf, nf)},
                     "인용제외": {"pos": pnq, "neg": nnq, "index": idx(pnq, nnq)},
                     "인용에서_온_평가어": dict(quoted.most_common(6)), "kwic": kwic}
    return result


def naming_dispersion(corpus):
    """경쟁 명명어 시기별 빈도(만자당)·문서빈도 + 미래파 핵심명명/미언급 비율."""
    res = {"terms": {}, "target_share": {}}
    for term in C.NAMING_TERMS:
        row = {}
        for p in corpus.periods():
            docs = corpus.period_docs(p)
            chars = sum(len(d.text.replace(" ", "")) for d in docs) or 1
            occ = sum(d.text.count(term) for d in docs)
            df = sum(1 for d in docs if term in d.text)
            row[p] = {"rate": round(occ / chars * 10000, 2), "docs": f"{df}/{len(docs)}"}
        res["terms"][term] = row
    for p in corpus.periods():
        docs = corpus.period_docs(p); n = len(docs)
        core = sum(1 for d in docs if d.text.count(C.TARGET) >= 5)
        zero = sum(1 for d in docs if d.text.count(C.TARGET) == 0)
        res["target_share"][p] = {"n": n, "핵심명명(>=5)": f"{core} ({core/n*100:.0f}%)",
                                  "미언급(0)": f"{zero} ({zero/n*100:.0f}%)"}
    return res
