---
id: elementary-math-topic-map
page_type: topic_map
status: reviewed
verified_at: 2026-06-27
---

# Elementary mathematics topic map

Topics select achievement standards inside an official grade band. Except for a separately reviewed semester override, `placement` remains `grade_band_only` and must not be presented as official semester placement.

```json math-topic-map
{
  "topics": [
    {"id":"m12-numbers-100","name":"100까지의 수","aliases":["0과 100까지의 수","100까지 수","수 세기"],"grade_band":"1-2","standards":["[2수01-01]"],"domain":"number_operations","profile":"number-concept","prerequisites":[]},
    {"id":"m12-four-digit-numbers","name":"네 자리 이하의 수","aliases":["네 자리 수","천까지의 수","1000까지의 수","수의 크기 비교"],"grade_band":"1-2","standards":["[2수01-02]","[2수01-03]"],"domain":"number_operations","profile":"number-concept","prerequisites":["m12-numbers-100"]},
    {"id":"m12-compose-decompose","name":"수의 분해와 합성","aliases":["수 가르기와 모으기","수의 합성과 분해"],"grade_band":"1-2","standards":["[2수01-04]"],"domain":"number_operations","profile":"number-concept","prerequisites":["m12-numbers-100"]},
    {"id":"m12-add-subtract","name":"덧셈과 뺄셈","aliases":["두 자리 수의 덧셈과 뺄셈","세 수의 덧셈과 뺄셈","덧셈식과 뺄셈식","덧셈 뺄셈"],"grade_band":"1-2","standards":["[2수01-05]","[2수01-06]","[2수01-07]","[2수01-08]","[2수01-09]"],"domain":"number_operations","profile":"operation","prerequisites":["m12-compose-decompose"]},
    {"id":"m12-multiplication","name":"곱셈","aliases":["곱셈구구","한 자리 수의 곱셈","구구단"],"grade_band":"1-2","standards":["[2수01-10]","[2수01-11]"],"domain":"number_operations","profile":"operation","prerequisites":["m12-add-subtract"]},
    {"id":"m12-patterns","name":"규칙 찾기","aliases":["규칙","무늬의 규칙","수 배열의 규칙"],"grade_band":"1-2","standards":["[2수02-01]","[2수02-02]"],"domain":"change_relations","profile":"pattern-relation","prerequisites":[]},
    {"id":"m12-solid-shapes","name":"입체도형의 모양","aliases":["여러 가지 모양","직육면체 원기둥 구","쌓기나무"],"grade_band":"1-2","standards":["[2수03-01]","[2수03-02]"],"domain":"geometry_measurement","profile":"spatial-construction","prerequisites":[]},
    {"id":"m12-plane-shapes","name":"평면도형의 모양","aliases":["삼각형 사각형 원","여러 가지 평면도형","도형의 모양"],"grade_band":"1-2","standards":["[2수03-03]","[2수03-04]","[2수03-05]"],"domain":"geometry_measurement","profile":"geometry-concept","prerequisites":[]},
    {"id":"m12-compare-quantities","name":"양의 비교","aliases":["길이 들이 무게 넓이 비교","여러 가지 양 비교"],"grade_band":"1-2","standards":["[2수03-06]"],"domain":"geometry_measurement","profile":"measurement","prerequisites":[]},
    {"id":"m12-time","name":"시각과 시간","aliases":["시계 보기","몇 시 몇 분","달력과 시간"],"grade_band":"1-2","standards":["[2수03-07]","[2수03-08]","[2수03-09]"],"domain":"geometry_measurement","profile":"measurement","prerequisites":["m12-numbers-100"]},
    {"id":"m12-length","name":"길이","aliases":["cm와 m","센티미터와 미터","길이 재기","길이의 덧셈과 뺄셈"],"grade_band":"1-2","standards":["[2수03-10]","[2수03-11]","[2수03-12]","[2수03-13]"],"domain":"geometry_measurement","profile":"measurement","prerequisites":["m12-compare-quantities","m12-add-subtract"]},
    {"id":"m12-tables-graphs","name":"분류·표·그래프","aliases":["분류하기","표와 그래프","자료를 표와 그래프로"],"grade_band":"1-2","standards":["[2수04-01]","[2수04-02]","[2수04-03]"],"domain":"data_chance","profile":"data","prerequisites":["m12-numbers-100"]},

    {"id":"m34-large-numbers","name":"큰 수","aliases":["10000 이상의 수","만 이상의 수","다섯 자리 수"],"grade_band":"3-4","standards":["[4수01-01]","[4수01-02]"],"domain":"number_operations","profile":"number-concept","prerequisites":["m12-four-digit-numbers"]},
    {"id":"m34-add-subtract","name":"세 자리 수의 덧셈과 뺄셈","aliases":["자연수의 덧셈과 뺄셈","세 자리 수 덧셈 뺄셈"],"grade_band":"3-4","standards":["[4수01-03]"],"domain":"number_operations","profile":"operation","prerequisites":["m12-add-subtract"]},
    {"id":"m34-multiplication","name":"자연수의 곱셈","aliases":["두 자리 수의 곱셈","세 자리 수의 곱셈","곱셈"],"grade_band":"3-4","standards":["[4수01-04]"],"domain":"number_operations","profile":"operation","prerequisites":["m12-multiplication"]},
    {"id":"m34-division","name":"자연수의 나눗셈","aliases":["나눗셈","몫과 나머지","두 자리 수로 나누기","한 자리 수로 나누기"],"grade_band":"3-4","standards":["[4수01-05]","[4수01-06]","[4수01-07]"],"domain":"number_operations","profile":"operation","prerequisites":["m12-multiplication"]},
    {"id":"m34-estimation","name":"어림셈","aliases":["자연수의 어림셈","어림하여 계산하기"],"grade_band":"3-4","standards":["[4수01-08]"],"domain":"number_operations","profile":"operation","prerequisites":["m34-add-subtract","m34-multiplication","m34-division"]},
    {"id":"m34-fraction-concept","name":"분수의 이해와 크기 비교","aliases":["분수","단위분수","진분수 가분수 대분수","분수의 크기 비교"],"grade_band":"3-4","standards":["[4수01-09]","[4수01-10]","[4수01-11]"],"domain":"number_operations","profile":"fraction-decimal-concept","prerequisites":["m12-compose-decompose"]},
    {"id":"m34-decimal-concept","name":"소수의 이해와 크기 비교","aliases":["소수","소수 한 자리 수","소수 두 자리 수","소수 세 자리 수","소수의 크기 비교"],"grade_band":"3-4","standards":["[4수01-12]","[4수01-13]","[4수01-14]"],"domain":"number_operations","profile":"fraction-decimal-concept","prerequisites":["m34-fraction-concept","m34-large-numbers"]},
    {"id":"m34-fraction-add-subtract","name":"분모가 같은 분수의 덧셈과 뺄셈","aliases":["분수의 덧셈과 뺄셈","분모 같은 분수 덧셈 뺄셈"],"grade_band":"3-4","standards":["[4수01-15]"],"domain":"number_operations","profile":"fraction-operation","prerequisites":["m34-fraction-concept"]},
    {"id":"m34-decimal-add-subtract","name":"소수의 덧셈과 뺄셈","aliases":["소수 덧셈 뺄셈","소수 두 자리 수의 덧셈과 뺄셈"],"grade_band":"3-4","standards":["[4수01-16]"],"domain":"number_operations","profile":"decimal-operation","prerequisites":["m34-decimal-concept","m34-add-subtract"]},
    {"id":"m34-patterns","name":"변화 규칙과 계산식의 규칙","aliases":["규칙 찾기","변화 규칙","계산식의 규칙"],"grade_band":"3-4","standards":["[4수02-01]","[4수02-02]"],"domain":"change_relations","profile":"pattern-relation","prerequisites":["m12-patterns"]},
    {"id":"m34-equality","name":"등호와 양의 관계","aliases":["등호","같은 두 양의 관계","등식"],"grade_band":"3-4","standards":["[4수02-03]"],"domain":"change_relations","profile":"pattern-relation","prerequisites":["m12-add-subtract"]},
    {"id":"m34-lines-angles","name":"선·각·수직·평행","aliases":["직선 선분 반직선","각과 직각","예각 둔각","수직과 평행"],"grade_band":"3-4","standards":["[4수03-01]","[4수03-02]","[4수03-03]"],"domain":"geometry_measurement","profile":"geometry-concept","prerequisites":["m12-plane-shapes"]},
    {"id":"m34-shape-transform","name":"도형의 이동","aliases":["밀기 뒤집기 돌리기","평면도형의 이동","점의 이동"],"grade_band":"3-4","standards":["[4수03-04]","[4수03-05]"],"domain":"geometry_measurement","profile":"spatial-construction","prerequisites":["m12-plane-shapes"]},
    {"id":"m34-circle","name":"원","aliases":["원의 중심 반지름 지름","컴퍼스로 원 그리기"],"grade_band":"3-4","standards":["[4수03-06]","[4수03-07]"],"domain":"geometry_measurement","profile":"geometry-concept","prerequisites":["m12-plane-shapes"]},
    {"id":"m34-triangles","name":"삼각형의 분류와 성질","aliases":["여러 가지 삼각형","이등변삼각형 정삼각형","직각삼각형 예각삼각형 둔각삼각형"],"grade_band":"3-4","standards":["[4수03-08]","[4수03-09]"],"domain":"geometry_measurement","profile":"geometry-concept","prerequisites":["m34-lines-angles"]},
    {"id":"m34-quadrilaterals","name":"사각형의 분류와 성질","aliases":["여러 가지 사각형","직사각형 정사각형 사다리꼴 평행사변형 마름모"],"grade_band":"3-4","standards":["[4수03-10]"],"domain":"geometry_measurement","profile":"geometry-concept","prerequisites":["m34-lines-angles"]},
    {"id":"m34-polygons","name":"다각형과 모양 만들기","aliases":["다각형","정다각형","도형 채우기","모양 만들기"],"grade_band":"3-4","standards":["[4수03-11]","[4수03-12]"],"domain":"geometry_measurement","profile":"spatial-construction","prerequisites":["m34-triangles","m34-quadrilaterals"]},
    {"id":"m34-time","name":"초 단위의 시각과 시간","aliases":["시각과 시간","1분과 1초","시간의 덧셈과 뺄셈"],"grade_band":"3-4","standards":["[4수03-13]","[4수03-14]"],"domain":"geometry_measurement","profile":"measurement","prerequisites":["m12-time","m34-add-subtract"]},
    {"id":"m34-length","name":"mm와 km의 길이","aliases":["길이","밀리미터와 킬로미터","mm km","길이 단위 관계"],"grade_band":"3-4","standards":["[4수03-15]","[4수03-16]"],"domain":"geometry_measurement","profile":"measurement","prerequisites":["m12-length"]},
    {"id":"m34-capacity","name":"들이","aliases":["L와 mL","리터와 밀리리터","들이의 덧셈과 뺄셈"],"grade_band":"3-4","standards":["[4수03-17]","[4수03-18]","[4수03-19]"],"domain":"geometry_measurement","profile":"measurement","prerequisites":["m12-compare-quantities","m34-add-subtract"]},
    {"id":"m34-mass","name":"무게","aliases":["g kg t","그램 킬로그램 톤","무게의 덧셈과 뺄셈"],"grade_band":"3-4","standards":["[4수03-20]","[4수03-21]","[4수03-22]","[4수03-23]"],"domain":"geometry_measurement","profile":"measurement","prerequisites":["m12-compare-quantities","m34-add-subtract"]},
    {"id":"m34-angle-measure","name":"각도와 내각의 합","aliases":["각도","각도기","삼각형 내각의 합","사각형 내각의 합"],"grade_band":"3-4","standards":["[4수03-24]","[4수03-25]"],"domain":"geometry_measurement","profile":"measurement","prerequisites":["m34-lines-angles","m34-triangles","m34-quadrilaterals"]},
    {"id":"m34-graphs","name":"그림그래프·막대그래프·꺾은선그래프","aliases":["그래프","그림그래프","막대그래프","꺾은선그래프","자료 조사"],"grade_band":"3-4","standards":["[4수04-01]","[4수04-02]","[4수04-03]"],"domain":"data_chance","profile":"data","prerequisites":["m12-tables-graphs"]},

    {"id":"m56-mixed-operations","name":"자연수의 혼합 계산","aliases":["혼합 계산","덧셈 뺄셈 곱셈 나눗셈 혼합"],"grade_band":"5-6","standards":["[6수01-01]"],"domain":"number_operations","profile":"operation","prerequisites":["m34-add-subtract","m34-multiplication","m34-division"]},
    {"id":"m56-number-range","name":"수의 범위","aliases":["이상 이하 초과 미만","수의 범위 나타내기"],"grade_band":"5-6","standards":["[6수01-02]"],"domain":"number_operations","profile":"number-concept","prerequisites":["m34-large-numbers"]},
    {"id":"m56-rounding","name":"올림·버림·반올림","aliases":["어림값","반올림","올림과 버림"],"grade_band":"5-6","standards":["[6수01-03]"],"domain":"number_operations","profile":"operation","prerequisites":["m34-estimation","m34-decimal-concept"]},
    {"id":"m56-factors-multiples","name":"약수와 배수","aliases":["약수 공약수 최대공약수","배수 공배수 최소공배수","최대공약수와 최소공배수"],"grade_band":"5-6","standards":["[6수01-04]","[6수01-05]"],"domain":"number_operations","profile":"number-concept","prerequisites":["m12-multiplication","m34-division"]},
    {"id":"m56-fraction-equivalence","name":"약분·통분과 분수의 크기","aliases":["약분과 통분","크기가 같은 분수","분모가 다른 분수의 크기 비교"],"grade_band":"5-6","standards":["[6수01-06]","[6수01-07]"],"domain":"number_operations","profile":"fraction-decimal-concept","prerequisites":["m34-fraction-concept","m56-factors-multiples"]},
    {"id":"m56-fraction-add-subtract","name":"분모가 다른 분수의 덧셈과 뺄셈","aliases":["분수의 덧셈과 뺄셈","분모 다른 분수 덧셈 뺄셈"],"grade_band":"5-6","standards":["[6수01-08]"],"domain":"number_operations","profile":"fraction-operation","prerequisites":["m56-fraction-equivalence","m34-fraction-add-subtract"]},
    {"id":"m56-fraction-multiply","name":"분수의 곱셈","aliases":["분수 곱셈"],"grade_band":"5-6","standards":["[6수01-09]"],"domain":"number_operations","profile":"fraction-operation","prerequisites":["m34-fraction-concept","m34-multiplication"]},
    {"id":"m56-natural-quotient-fraction","name":"자연수 나눗셈의 몫을 분수로 나타내기","aliases":["나눗셈의 몫을 분수로","자연수 나누기 자연수와 분수"],"grade_band":"5-6","standards":["[6수01-10]"],"domain":"number_operations","profile":"fraction-decimal-concept","prerequisites":["m34-division","m34-fraction-concept"]},
    {"id":"m56-fraction-division","name":"분수의 나눗셈","aliases":["분수 나눗셈"],"grade_band":"5-6","standards":["[6수01-11]"],"domain":"number_operations","profile":"fraction-operation","prerequisites":["m56-fraction-multiply","m56-natural-quotient-fraction"]},
    {"id":"m56-fraction-decimal-relation","name":"분수와 소수의 관계","aliases":["분수와 소수","분수 소수 크기 비교","분수를 소수로","소수를 분수로"],"grade_band":"5-6","standards":["[6수01-12]"],"domain":"number_operations","profile":"fraction-decimal-concept","prerequisites":["m34-fraction-concept","m34-decimal-concept"]},
    {"id":"m56-decimal-multiply","name":"소수의 곱셈","aliases":["소수 곱셈"],"grade_band":"5-6","standards":["[6수01-13]"],"domain":"number_operations","profile":"decimal-operation","prerequisites":["m34-decimal-add-subtract","m34-multiplication"]},
    {"id":"m56-natural-quotient-decimal","name":"자연수 나눗셈의 몫을 소수로 나타내기","aliases":["나눗셈의 몫을 소수로","자연수 나누기 자연수와 소수"],"grade_band":"5-6","standards":["[6수01-14]"],"domain":"number_operations","profile":"fraction-decimal-concept","prerequisites":["m34-division","m34-decimal-concept"]},
    {"id":"m56-decimal-division","name":"소수의 나눗셈","aliases":["소수 나눗셈"],"grade_band":"5-6","standards":["[6수01-14]","[6수01-15]"],"domain":"number_operations","profile":"decimal-operation","prerequisites":["m34-division","m34-decimal-concept","m56-natural-quotient-decimal"]},
    {"id":"m56-correspondence","name":"대응 관계","aliases":["두 양의 대응 관계","대응 관계를 식으로","표에서 규칙 찾기"],"grade_band":"5-6","standards":["[6수02-01]"],"domain":"change_relations","profile":"pattern-relation","prerequisites":["m34-patterns","m34-equality"]},
    {"id":"m56-ratio-rate","name":"비와 비율","aliases":["비","비율","백분율","비율을 분수 소수 백분율로"],"grade_band":"5-6","standards":["[6수02-02]","[6수02-03]"],"domain":"change_relations","profile":"fraction-decimal-concept","prerequisites":["m56-fraction-decimal-relation"]},
    {"id":"m56-proportion","name":"비례식과 비례배분","aliases":["비례식","비례배분"],"grade_band":"5-6","standards":["[6수02-04]","[6수02-05]"],"domain":"change_relations","profile":"pattern-relation","prerequisites":["m56-ratio-rate","m56-correspondence"]},
    {"id":"m56-congruence-symmetry","name":"합동과 대칭","aliases":["도형의 합동","선대칭도형","점대칭도형","대칭"],"grade_band":"5-6","standards":["[6수03-01]","[6수03-02]"],"domain":"geometry_measurement","profile":"geometry-concept","prerequisites":["m34-shape-transform","m34-polygons"]},
    {"id":"m56-rectangular-prisms","name":"직육면체와 정육면체","aliases":["직육면체 정육면체","겨냥도","직육면체 전개도"],"grade_band":"5-6","standards":["[6수03-03]","[6수03-04]"],"domain":"geometry_measurement","profile":"spatial-construction","prerequisites":["m12-solid-shapes","m34-polygons"]},
    {"id":"m56-prisms-pyramids","name":"각기둥과 각뿔","aliases":["각기둥 각뿔","각기둥의 전개도"],"grade_band":"5-6","standards":["[6수03-05]","[6수03-06]"],"domain":"geometry_measurement","profile":"spatial-construction","prerequisites":["m56-rectangular-prisms","m34-polygons"]},
    {"id":"m56-round-solids","name":"원기둥·원뿔·구","aliases":["원기둥 원뿔 구","원기둥의 전개도"],"grade_band":"5-6","standards":["[6수03-07]","[6수03-08]"],"domain":"geometry_measurement","profile":"spatial-construction","prerequisites":["m12-solid-shapes","m34-circle"]},
    {"id":"m56-blocks","name":"쌓기나무와 공간","aliases":["쌓기나무","위 앞 옆에서 본 모양","쌓기나무 개수"],"grade_band":"5-6","standards":["[6수03-09]","[6수03-10]"],"domain":"geometry_measurement","profile":"spatial-construction","prerequisites":["m12-solid-shapes"]},
    {"id":"m56-perimeter-area","name":"둘레와 다각형의 넓이","aliases":["둘레와 넓이","평면도형의 둘레","직사각형 정사각형 넓이","평행사변형 삼각형 사다리꼴 마름모 넓이"],"grade_band":"5-6","standards":["[6수03-11]","[6수03-12]","[6수03-13]","[6수03-14]"],"domain":"geometry_measurement","profile":"measurement","prerequisites":["m34-length","m34-polygons"]},
    {"id":"m56-circle-measure","name":"원주율·원주·원의 넓이","aliases":["원주율","원주","원의 둘레","원의 넓이"],"grade_band":"5-6","standards":["[6수03-15]","[6수03-16]"],"domain":"geometry_measurement","profile":"measurement","prerequisites":["m34-circle","m56-decimal-multiply"]},
    {"id":"m56-surface-volume","name":"겉넓이와 부피","aliases":["직육면체 겉넓이","직육면체 부피","정육면체 겉넓이와 부피","부피 단위"],"grade_band":"5-6","standards":["[6수03-17]","[6수03-18]","[6수03-19]"],"domain":"geometry_measurement","profile":"measurement","prerequisites":["m56-rectangular-prisms","m56-perimeter-area"]},
    {"id":"m56-average","name":"평균","aliases":["자료의 평균","평균 구하기"],"grade_band":"5-6","standards":["[6수04-01]"],"domain":"data_chance","profile":"data","prerequisites":["m34-graphs","m34-division"]},
    {"id":"m56-band-circle-graphs","name":"띠그래프와 원그래프","aliases":["띠그래프","원그래프","자료에 알맞은 그래프"],"grade_band":"5-6","standards":["[6수04-02]","[6수04-03]"],"domain":"data_chance","profile":"data","prerequisites":["m34-graphs","m56-ratio-rate"]},
    {"id":"m56-probability","name":"가능성","aliases":["사건이 일어날 가능성","가능성 비교","가능성을 수로","자료로 가능성 예상"],"grade_band":"5-6","standards":["[6수04-04]","[6수04-05]","[6수04-06]"],"domain":"data_chance","profile":"probability","prerequisites":["m34-graphs","m56-fraction-decimal-relation"]}
  ],
  "placement": "grade_band_only",
  "allowed_shared_standards": ["[6수01-14]"]
}
```
