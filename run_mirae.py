#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_mirae.py — 미래파 분석 실행 (gigyo run_*.py 관례 준용)

  python run_mirae.py
결과: 콘솔 요약 + 미래파_분석_확장/mirae_report.txt (UTF-8)
"""
import os
from mirae import build_corpus, analyses, config as C

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "mirea_clean")  # 정제본(clean_corpus.py 산출). 원본=mirea_results
OUT = os.path.join(HERE, "미래파_분석_확장", "mirae_report.txt")


def main():
    print("코퍼스 로딩(Kiwi 형태소)...")
    corp = build_corpus(SRC)
    s = corp.summary()
    L = []
    def w(x=""): L.append(str(x))

    w("=" * 60); w("미래파 논쟁 — 체계적 분석 리포트"); w("=" * 60)
    w(f"문서 {s['docs']}편 · 내용어 토큰 {s['tokens']:,} · 진영 {s['camps']}")
    w("시기별 문서수: " + ", ".join(f"{p.split()[0]}={n}" for p, n in s["by_period"].items()))

    # ── 1. 명명 분산 (Q1) ─────────────────────────────
    w("\n[1] 경쟁 명명어 분산 (만자당 빈도 · 문서빈도)")
    nd = analyses.naming_dispersion(corp)
    ps = corp.periods()
    w("  " + " " * 10 + "".join(f"{p.split()[0]:>12}" for p in ps))
    for term, row in nd["terms"].items():
        w(f"  {term:<10}" + "".join(f"{row[p]['rate']:>7}({row[p]['docs']:>4})" for p in ps))
    w("\n  · '미래파' 호명 비율:")
    for p in ps:
        t = nd["target_share"][p]
        w(f"    {p}: n={t['n']} · 핵심명명 {t['핵심명명(>=5)']} · 미언급 {t['미언급(0)']}")

    # ── 2. 시기별 키워드성 (Q1/Q3) ────────────────────
    w("\n[2] 시기별 키워드성 (해당 시기 vs 나머지, LL)")
    ky = analyses.keyness_by_period(corp)
    for p, r in ky.items():
        rel = "" if r["reliable"] else "  ⚠셀 신뢰성 낮음"
        w(f"  · {p}  (문서 {r['n_docs']}, 토큰 {r['n_tokens']:,}){rel}")
        top = r["keywords"][:12]
        w("    " + ", ".join(f"{k['word']}(LL{k['ll']},{k['docs']}){k['flag']}" for k in top))

    # ── 3. 담화 운율 (Q2) — 전체 vs 인용제외 ──────────
    w("\n[3] '미래파' 담화 운율 — 전체 vs 인용(<quote>)제외")
    pr = analyses.discourse_prosody(corp)
    w("  " + f"{'시기':<22}{'문장':>5}{'전체(긍/부/지수)':>18}{'인용제외(긍/부/지수)':>20}")
    for p, r in pr.items():
        f_, q_ = r["전체"], r["인용제외"]
        w(f"  {p:<22}{r['n_sents']:>5}  {f_['pos']:>3}/{f_['neg']:<3}{f_['index']:>+5}   "
          f"    {q_['pos']:>3}/{q_['neg']:<3}{q_['index']:>+5}")
    w("\n  · 인용에서 온(=화자 아닌) 평가어 예:")
    for p, r in pr.items():
        if r["인용에서_온_평가어"]:
            w(f"    {p.split()[0]}: " + ", ".join(f"{k}×{v}" for k, v in r["인용에서_온_평가어"].items()))
    w("\n  · KWIC 표본(평가어 포함; [인용에서]=quote에서만 온 것 → 표적 오염 의심):")
    for p, r in pr.items():
        for k in r["kwic"][:2]:
            tag = f"+{','.join(k['pos'])} -{','.join(k['neg'])}"
            q = f" [인용에서:{','.join(k['인용에서'])}]" if k["인용에서"] else ""
            w(f"    [{p.split()[0]}] ({tag}){q} {k['author']}: {k['text']}...")

    w("\n" + "=" * 60)
    w("주의: LL은 소표본이라 절대값보다 순위로 해석. 운율지수는 지표일 뿐,")
    w("      반드시 KWIC로 표적 확인(인용제외 열·[인용에서] 태그 참조).")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print("완료 →", OUT)
    print(f"  문서 {s['docs']} · 토큰 {s['tokens']:,}")


if __name__ == "__main__":
    main()
