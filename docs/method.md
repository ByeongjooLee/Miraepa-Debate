# 방법 개요 (Method)

이 저장소는 TEI로 태깅된 비평 코퍼스를 입력으로 받아 코퍼스 기반 담화분석(CADS,
Corpus-Assisted Discourse Studies; Baker 2006, Partington 2004)을 수행한다. 태깅
자체는 상위 저장소 [KOR-criticism-autoTagging](https://github.com/eiloppang/KOR-criticism-autoTagging)의
**추출 후 조립(extract-then-assemble) 아키텍처**가 담당한다 — LLM은 개체 식별과 의미
판단만 하고, 문서 구조의 생성·검증은 결정론적 코드가 통제하며, 산출된 태그는 연구자가
전수 검수·확정한다.

## 입력: 도메인 특화 TEI 스키마

`schema/korean-critique-schema-v5.xsd`가 규정하는 일곱 인라인 개체를 사용한다.

| 개체 | 뜻 | 주요 속성 |
|---|---|---|
| `persName` | 실명 인물 | `role` (critic/poet/foreigner …) |
| `title` | 작품·저작·매체명 | `level`, `type` |
| `orgName` | 기관·매체사 | |
| `term` | 비평 개념어 | `type` (concept/movement) |
| `quote` | 인용(따옴표·시 인용) | `type`, `genre`, `source` |
| `interp` | 비평가의 가치판단 | `value` (affirmative/neutral/critical), `ana` |
| `date` | 연도·날짜 | `when` |

## 분석 도구 (mirae/analyses.py)

1. **공기어(collocation)** — 대상어 좌우 ±5어 창의 공기 빈도 + 로그우도(LL)·상호정보량(MI).
2. **키워드성(keyness)** — 하위 코퍼스(시기·진영) 대 나머지의 과대출현 어휘를 LL로.
3. **명명 분산(naming dispersion)** — 대상어와 경쟁 명명어의 시기·진영별 분포, 1만 자당 빈도, 호명률.
4. **담화 운율(discourse prosody)** — 대상어 주변 평가어 사전(POS_EVAL/NEG_EVAL) 집계.
   `<quote>` 구간을 분리해 '인용된 비판'의 오염을 통제한다.
5. **진영별 대조(camp contrast)** — `CAMP_MAP`으로 배정한 옹호/비판 하위 코퍼스 비교
   (변별 어휘, 인용 장르 구성, 판단(interp) 분포).

## 읽기 원칙

- **모든 공기·키워드 수치는 문서빈도(df)와 함께 읽는다.** 한 저자가 한 글에서 반복한
  어휘는 LL·공기빈도를 체계적으로 부풀린다(LL은 각 출현을 독립 사건으로 가정). df가
  낮은 값은 담론·시기 경향이 아니라 개별 텍스트의 근거로만 취한다.
- **소표본에서 LL은 유의성 검정이 아니라 상대 순위·방향의 지표**로만 읽는다.
- **담화 운율은 태도의 결론이 아니라 가설 제시 도구**다. 대상어 주변 평가어가 실제로
  무엇을 겨냥하는지는 반드시 KWIC 정독으로 확인한다.
- **진영(camp) 배정은 해석적·연구자 의존 절차**다. interp 분포와 진영의 상관은 독립적
  검증이 아니라 정합성의 확인으로 읽는다.

## 다른 논쟁에 적용

원칙적으로 `mirae/config.py`만 수정한다. `TARGET`(대상 기표), `NAMING_TERMS`(경쟁
명명어), `KEY_TERMS`(개념어 사전), `POS_EVAL`/`NEG_EVAL`(평가어 사전), `period()`(시기
구분), `CAMP_MAP`(진영 배정)을 자신의 코퍼스에 맞게 바꾸면 된다. 로직(corpus.py /
analyses.py)은 config에 단방향으로 의존한다.

## 참고문헌

- Baker, P. (2006). *Using Corpora in Discourse Analysis*. Continuum.
- Partington, A. (2004). "Corpora and Discourse, a Most Congruous Beast." In *Corpora and Discourse*. Peter Lang.
- 관련 논문(미래파 논쟁 사례연구)은 투고/게재 예정.
