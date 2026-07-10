# Miraepa-Debate

**기계로 읽는 '미래파' 논쟁 — 한국 현대문학비평의 코퍼스 기반 담화분석(CADS) 도구**
Corpus-Assisted Discourse Studies for Korean literary criticism (the 2000s *Miraepa* debate).

TEI로 태깅된 비평 코퍼스를 입력받아, 공기어(collocation)·키워드성(keyness)·명명 분산(naming dispersion)·담화 운율(discourse prosody)·진영별 대조(camp contrast)를 계산하고, 거시 통계와 미시 정독(KWIC)을 오가며 하나의 문학 논쟁을 분석한다. 논문 「기계로 읽는 '미래파' 논쟁」(2000년대 한국 시단의 미래파 논쟁 사례연구)의 분석 코드다.

> **태깅은 이 저장소가 하지 않는다.** 입력이 되는 TEI 비평 코퍼스는 상위 저장소
> [**eiloppang/KOR-criticism-autoTagging**](https://github.com/eiloppang/KOR-criticism-autoTagging)
> (추출 후 조립 아키텍처, LLM 보조 태깅)이 생성한다. 이 저장소는 그 산출물을 **읽는** 분석층이다.

---

## 파이프라인에서의 위치

```
원문(문예지 스캔) ──OCR──▶ 정제 텍스트 ──[KOR-criticism-autoTagging]──▶ TEI/XML 코퍼스
                                                                            │
                                                          이 저장소 (CADS 분석) ◀┘
                                          collocation · keyness · dispersion · prosody · camp
```

## 구성

```
Miraepa-Debate/
├── mirae/                     # 핵심 분석 패키지
│   ├── config.py              #   설정 — 대상어·경쟁 명명어·개념어/평가어 사전·시기·진영(camp)
│   ├── corpus.py              #   TEI/XML 로더 (Kiwi 토큰화, <quote> 분리, 문장 단위 KWIC)
│   └── analyses.py            #   로그우도·키워드성·담화 운율·명명 분산
├── run_mirae.py               # ▶ 메인 실행: 전체 분석 → 리포트
├── scripts/
│   ├── analysis/              # 개별 분석·데모 (독립 실행)
│   │   ├── kwic_demo.py           KWIC 용례 추출
│   │   ├── prosody_demo.py        담화 운율 데모
│   │   ├── h4_keyword_trajectory.py  키워드 통시 궤적
│   │   ├── per_year.py / periodize.py  연도·시기 분할
│   │   ├── profile_data.py        코퍼스 기초 통계
│   │   └── analyze_misraepa.py    통합 분석(초기 버전)
│   ├── viewers/              # 태그 검수용 HTML 뷰어 생성
│   │   ├── render_tags.py
│   │   ├── build_editor.py
│   │   └── build_html_by_period.py
│   └── corpus_prep/          # OCR 정제·품질 측정
│       ├── clean_corpus.py
│       ├── ocr_audit.py
│       └── ocr_quality.py
├── schema/
│   └── korean-critique-schema-v5.xsd   # 입력 TEI가 준수하는 도메인 스키마
├── examples/
│   └── sample_2010_v2.xml     # 합성 태깅 예시 1건 (저작권 무관, 시험용)
└── docs/method.md             # 방법 상세
```

`run_mirae.py`만 `mirae/` 패키지를 사용하며(저장소 루트에서 실행), `scripts/` 아래 스크립트는
모두 독립 실행이다. 뷰어 두 개(`build_html_by_period.py` ← `build_editor.py`)는 같은 폴더에서
함께 동작한다.

## 설치

```bash
pip install -r requirements.txt   # kiwipiepy
```

## 사용

이 저장소는 **분석 대상 코퍼스를 포함하지 않는다**(아래 데이터 이용 안내 참조).
직접 준비한 TEI/XML 코퍼스 폴더를 지정해 실행한다.

```bash
# 저장소 루트에서 실행

# 1) 전체 분석 (SRC 경로를 examples/ 등 본인 코퍼스로 수정)
python run_mirae.py

# 2) 개별 분석·데모
python scripts/analysis/kwic_demo.py
python scripts/analysis/prosody_demo.py

# 3) 진영·시기·대상어는 mirae/config.py에서 조정
```

`mirae/config.py`의 `CAMP_MAP`(진영 배정), `period()`(시기 구분), `TARGET`·`NAMING_TERMS`·`KEY_TERMS`(대상·명명·개념어)를 자신의 논쟁에 맞게 바꾸면 다른 비평 논쟁에도 적용할 수 있다.

## 데이터 이용 안내 (Data availability)

분석 대상인 2000년대 시 비평 원문(문예지 수록분)과 그로부터 파생된 태깅 코퍼스는
**저작권 보호 대상이므로 이 저장소에 포함하지 않는다.** 따라서 **방법(코드)은 완전히
재현 가능하되, 원자료를 이용한 결과 전체의 재현에는 제약이 따른다.** 파이프라인 동작
확인을 위해 저작권과 무관한 합성 예시(`examples/sample_2010_v2.xml`) 한 건을 제공한다.

다만 평가(interp) 판정의 근거를 독자가 확인할 수 있도록, 각 비평문에서 **문서당 긍정·부정
각 최대 3문장**만 출처와 함께 발췌한 [`supplementary/interp_excerpt_posneg3.html`](supplementary/interp_excerpt_posneg3.html)
을 제공한다(개별 저작물 대비 소량 발췌·출처 명시·삭제 요청 안내 포함). 상세는
[`supplementary/README.md`](supplementary/README.md) 참조.

## 방법 개요

`docs/method.md` 참조. 핵심 원칙: 모든 공기·키워드 수치는 **문서빈도(df)와 함께** 읽어
단일 문서 편중을 노출하며, 거시 통계는 결론이 아니라 **정독할 지점을 지목**하는 데 쓴다.

## 인용

관련 논문은 투고/게재 예정이다. 확정 시 서지 정보를 추가한다.

---

### English (brief)

CADS toolkit for Korean literary criticism. It consumes TEI-tagged critical essays
produced by the upstream tagger
[eiloppang/KOR-criticism-autoTagging](https://github.com/eiloppang/KOR-criticism-autoTagging)
and computes collocation, keyness, naming dispersion, discourse prosody, and camp-based
contrast, always reading frequencies together with **document frequency (df)** to expose
single-document skew. The criticism corpus itself is **copyrighted and not included**; a
single synthetic example is provided so the pipeline can be run.
