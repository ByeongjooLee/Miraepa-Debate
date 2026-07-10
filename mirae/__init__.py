# -*- coding: utf-8 -*-
"""mirae — 미래파 논쟁 분석 패키지 (Critical-Debates/gigyo 구조 준용)."""
from . import config, analyses
from .corpus import Corpus


def build_corpus(src_dir: str) -> Corpus:
    return Corpus(src_dir).load()
