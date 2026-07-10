# -*- coding: utf-8 -*-
"""
corpus.py — TEI/XML 코퍼스 로더 (Kiwi 토큰화)

기교주의(plain text/비평가별)와 달리 미래파는 TEI/XML(다수 비평가·시기)이므로
전용 로더를 둔다. 핵심 안전장치:
  · 인용(<quote>) 제외 텍스트를 따로 보관 → 담화 운율의 '인용된 비판' 오염 방지
  · 시기(period)·(선택)진영(camp) 단위 토큰 그룹
  · 문장(<s>) 단위 접근 + 인용여부 플래그 → KWIC/표적 검증
"""
from __future__ import annotations
import os, glob
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple
from . import config as C

NS = "{http://www.tei-c.org/ns/1.0}"
def _ln(t): return t.split("}", 1)[-1] if "}" in t else t


def _meta(fn: str) -> Tuple[str, int]:
    b = fn[:-4]
    if b.endswith("_v2"): b = b[:-3]
    ps = b.split("_")
    for k, v in C.YEAR_OVERRIDE.items():   # 연도 있어도 우선 보정
        if fn.startswith(k): return ps[0], v
    y = next((int(p) for p in ps if p.isdigit() and len(p) == 4), 0)
    if y == 0:
        for k, v in C.YEAR_FIX.items():
            if fn.startswith(k): y = v; break
    return ps[0], y


def _text_full(el) -> str:
    return "".join(el.itertext())


def _text_noquote(el) -> str:
    """<quote> 하위 텍스트를 제외한 본문(비평가 자신의 발화)."""
    parts = [el.text or ""]
    for ch in el:
        if _ln(ch.tag) == "quote":
            parts.append(ch.tail or "")            # 인용 내용은 버리고 tail만
        else:
            parts.append(_text_noquote(ch)); parts.append(ch.tail or "")
    return "".join(parts)


class Doc:
    __slots__ = ("author", "year", "period", "camp", "text", "text_nq",
                 "sents", "tokens", "tokens_nq")
    def __init__(s, author, year, period, camp, text, text_nq, sents):
        s.author, s.year, s.period, s.camp = author, year, period, camp
        s.text, s.text_nq, s.sents = text, text_nq, sents
        s.tokens: List[str] = []; s.tokens_nq: List[str] = []


class Corpus:
    def __init__(self, src_dir: str):
        self.src = src_dir
        self.docs: List[Doc] = []
        self._kiwi = None

    # ── 로드 ──────────────────────────────────────────────
    def load(self) -> "Corpus":
        from kiwipiepy import Kiwi
        self._kiwi = Kiwi()
        for fp in sorted(glob.glob(os.path.join(self.src, "*.xml"))):
            fn = os.path.basename(fp)
            author, year = _meta(fn)
            if not year: continue
            if year > C.YEAR_MAX: continue   # 분석 범위 2005–2011
            try:
                body = ET.parse(fp).getroot().find(f"{NS}text/{NS}body")
            except Exception:
                continue
            if body is None: continue
            camp = next((v for k, v in C.CAMP_MAP.items() if fn.startswith(k)), None)
            # 문장 단위 (인용여부 플래그)
            sents = []
            for sen in body.iter(f"{NS}s"):
                st = _text_full(sen)
                snq = _text_noquote(sen)
                sents.append({"text": st, "text_nq": snq})
            d = Doc(author, year, C.period(year), camp,
                    _text_full(body), _text_noquote(body), sents)
            d.tokens = self._tok(d.text)
            d.tokens_nq = self._tok(d.text_nq)
            self.docs.append(d)
        return self

    def _tok(self, text: str) -> List[str]:
        return [t.form for t in self._kiwi.tokenize(text)
                if t.tag in C.CONTENT_TAGS and (len(t.form) > 1 or t.form in C.KEY_TERMS)]

    # ── 그룹 접근 ─────────────────────────────────────────
    def periods(self) -> List[str]:
        return [p for p in C.PERIOD_ORDER if any(d.period == p for d in self.docs)]

    def period_docs(self, p): return [d for d in self.docs if d.period == p]
    def period_tokens(self, p):
        out = []; [out.extend(d.tokens) for d in self.period_docs(p)]; return out
    def all_tokens(self):
        out = []; [out.extend(d.tokens) for d in self.docs]; return out
    def camps(self):
        return sorted({d.camp for d in self.docs if d.camp})
    def camp_tokens(self, camp):
        out = []; [out.extend(d.tokens) for d in self.docs if d.camp == camp]; return out

    # ── 문장 검색 (KWIC/운율용) ───────────────────────────
    def sents_with(self, term: str, by_period=True):
        """term 포함 문장을 (period -> [ {author,text,text_nq} ]) 로."""
        out = defaultdict(list)
        for d in self.docs:
            for s in d.sents:
                if term in s["text"]:
                    key = d.period if by_period else "ALL"
                    out[key].append({"author": d.author, "text": s["text"], "text_nq": s["text_nq"]})
        return out

    def summary(self):
        pc = Counter(d.period for d in self.docs)
        return {"docs": len(self.docs),
                "by_period": {p: pc[p] for p in self.periods()},
                "tokens": len(self.all_tokens()),
                "camps": self.camps() or "(미배정)"}
