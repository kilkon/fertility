# -*- coding: utf-8 -*-
"""Build chapter/section pages and chart datasets for the population book."""

from __future__ import annotations

import json
import numpy as np
import re
import site
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

USER_SITE = site.getusersitepackages()
if USER_SITE and USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DERIVED = DATA / "derived"
CHAPTERS = ROOT / "chapters"
SECTIONS = ROOT / "sections"
MANUSCRIPTS = ROOT / "manuscripts"
CHAPTER_MANUSCRIPTS = MANUSCRIPTS / "chapters"
SECTION_MANUSCRIPTS = MANUSCRIPTS / "sections"
APPENDIX_FILE = "appendix-data-notes.html"
ASSET_VERSION = "20260509-elderly-activity-supplement"
GITHUB_REPO_URL = "https://github.com/kilkon/fertility"


BOOK = [
    {
        "no": "0",
        "title": "왜 이 책을 썼는가",
        "file": "chapter-0.html",
        "thesis": "정책 진단이 추상적인 제안으로 끝나지 않으려면, 인구 변화를 데이터로 점검하고 정책의 실제 작동 조건을 차갑게 확인해야 한다.",
        "sections": [],
    },
    {
        "no": "1",
        "title": "지표의 함정과 인구를 읽는 방법",
        "file": "chapter-1.html",
        "thesis": "같은 인구 문제도 어떤 지표로 보느냐에 따라 전혀 다른 결론이 나온다.",
        "sections": [
            {
                "no": "1.1",
                "title": "인구피라미드는 무엇을 드러내는가",
                "file": "section-1-1-age-structure.html",
                "chart": "population_pyramid_four_panel",
            },
            {
                "no": "1.2",
                "title": "인구 기준은 왜 서로 다른가",
                "file": "section-1-2-population-measures.html",
                "chart": "population_measure_comparison",
            },
            {
                "no": "1.3",
                "title": "왜 갑자기 2010년에 인구가 증가했는가",
                "file": "section-1-3-2010-registration-jump.html",
                "chart": "resident_registration_2010_jump",
            },
            {
                "no": "1.4",
                "title": "인구가 많아야 하는 이유가 있는가",
                "file": "section-1-3-optimal-population.html",
                "chart": None,
            },
            {
                "no": "1.5",
                "title": "출산율은 어떻게 다양하게 측정되는가",
                "file": "section-1-4-fertility-measures.html",
                "chart": "fertility_measure_summary",
            },
        ],
    },
    {
        "no": "2",
        "title": "인구는 정말 감소하는가",
        "file": "chapter-2-population-decline.html",
        "thesis": "전국 인구 감소는 모든 지역이 동시에 줄어든다는 뜻이 아니다. 같은 20년 동안에도 성장축과 축소축이 함께 만들어진다.",
        "sections": [
            {
                "no": "2.1",
                "title": "인구가 증가한 지역은",
                "file": "section-2-1-population-growth-regions.html",
                "chart": "sigungu_population_slope_map",
            },
            {
                "no": "2.2",
                "title": "고령층 인구가 증가했는가",
                "file": "section-2-2-older-population-growth.html",
                "chart": "sigungu_older_population_slope_map",
            },
            {
                "no": "2.3",
                "title": "생산연령인구는 증가했는가",
                "file": "section-2-3-working-age-population-growth.html",
                "chart": "sigungu_working_age_population_slope_map",
            },
            {
                "no": "2.4",
                "title": "인구 집중도는 심화되는가",
                "file": "section-2-2-population-concentration.html",
                "chart": "sigungu_population_concentration",
            },
            {
                "no": "2.5",
                "title": "저출산은 한국만의 문제인가",
                "file": "section-2-5-international-low-fertility.html",
                "chart": "international_tfr_asia",
            },
        ],
    },
    {
        "no": "3",
        "title": "저출산 정책의 성과는 어떻게 평가해야 하는가",
        "file": "chapter-2.html",
        "thesis": "저출산 정책은 출산율 반등만이 아니라 출생아 수, 코호트 잔존, 정주 조건, 재정 투입을 함께 놓고 평가해야 한다.",
        "sections": [
            {
                "no": "3.1",
                "title": "저출산 정책은 어떤 것이 있는가",
                "file": "section-2-0-low-fertility-policy-types.html",
                "chart": "low_fertility_policy_typology",
            },
            {
                "no": "3.2",
                "title": "저출산 정책이 성공한 나라는 있는가",
                "file": "section-2-0-international-policy-success.html",
                "chart": "pronatalist_policy_country_comparison",
            },
            {
                "no": "3.3",
                "title": "주거 지원은 과연 결혼과 출산을 늘리고 있는가",
                "file": "section-2-1-housing-support-marriage-birth.html",
                "chart": "housing_support_policy_budget",
            },
            {
                "no": "3.4",
                "title": "지역 출산정책은 실제 인구를 남기는가",
                "file": "section-2-1-yeonggwang-cohort.html",
                "chart": "birth_incentive_region_retention",
            },
            {
                "no": "3.5",
                "title": "출산을 미루는 조건은 무엇인가",
                "file": "section-2-2-fertility-conditions.html",
                "chart": "fertility_age_pattern",
            },
        ],
    },
    {
        "no": "4",
        "title": "이동과 지역 격차가 인구를 다시 쓴다",
        "file": "chapter-3.html",
        "thesis": "출생만으로 지역 인구를 설명할 수 없다. 청년 이동, 외국인 유입, 국제결혼, 다문화 출생이 지역별 인구구조를 다시 만든다.",
        "sections": [
            {
                "no": "4.1",
                "title": "생활인구는 얼마나 클까",
                "file": "section-3-0-living-population.html",
                "chart": "living_population_ratio_top",
            },
            {
                "no": "4.2",
                "title": "어느 광역시도의 인구 순이동이 가장 큰가",
                "file": "section-3-0-sido-net-migration.html",
                "chart": "sido_net_migration_panel",
            },
            {
                "no": "4.3",
                "title": "청년 이동과 시군구 격차",
                "file": "section-3-1-regional-gap.html",
                "chart": "sigungu_aging_top",
            },
            {
                "no": "4.4",
                "title": "외국인·다문화·국제결혼",
                "file": "section-3-2-foreign-multicultural.html",
                "chart": "multicultural_birth_rate",
            },
        ],
    },
    {
        "no": "5",
        "title": "출산 결정의 생활시간표",
        "file": "chapter-4.html",
        "thesis": "출산 결정은 어느 날 갑자기 내려지는 선택이 아니라 독립, 주거, 혼인, 임신·출산, 돌봄 복귀가 이어지는 생활시간표 위에서 만들어진다.",
        "sections": [
            {
                "no": "5.1",
                "title": "결혼과 출산은 왜 문화적 현상인가",
                "file": "section-4-1-marriage-culture.html",
                "chart": "marriage_attitude_unmarried_gender",
            },
            {
                "no": "5.2",
                "title": "혼인·이혼·출생의 연결",
                "file": "section-4-1-family-formation.html",
                "chart": "vital_events_policy",
            },
            {
                "no": "5.3",
                "title": "이혼의 두려움은 결혼을 막는가",
                "file": "section-4-1-divorce-fear-marriage.html",
                "chart": "divorce_rate_30s_40s_trend",
            },
            {
                "no": "5.4",
                "title": "가구 수는 왜 인구와 다르게 움직이는가",
                "file": "section-4-5-households.html",
                "chart": "household_population_gap_national",
            },
            {
                "no": "5.5",
                "title": "주거 수요는 왜 인구보다 늦게 변하는가",
                "file": "section-4-6-housing-demand.html",
                "chart": "future_households_policy",
            },
            {
                "no": "5.6",
                "title": "남성이 육아를 담당하지 않는다?",
                "file": "section-4-2-men-care-parental-leave.html",
                "chart": "parental_leave_gender_users",
            },
            {
                "no": "5.7",
                "title": "돌봄과 일가정양립",
                "file": "section-4-3-care-work-balance.html",
                "chart": "childcare_children",
            },
            {
                "no": "5.8",
                "title": "어린이집이 적어서 출산을 덜 하는가",
                "file": "section-4-4-childcare-shortage.html",
                "chart": "childcare_supply_by_type",
            },
            {
                "no": "5.9",
                "title": "빈집은 생활권 약화의 신호인가",
                "file": "section-4-7-vacant-housing.html",
                "chart": "vacant_housing_policy",
            },
        ],
    },
    {
        "no": "6",
        "title": "고령사회, 노동시장, 재정의 압력",
        "file": "chapter-5.html",
        "thesis": "저출산·고령화의 마지막 질문은 누가 일하고 누가 돌봄과 비용을 감당하는가이다.",
        "sections": [
            {
                "no": "6.1",
                "title": "노동시장과 고령층 경제활동",
                "file": "section-5-1-labor-aging.html",
                "chart": "elderly_labor_dt_1de8031s",
            },
            {
                "no": "6.2",
                "title": "노령화 지수는 무엇이고 얼마나 빠르게 증가할까",
                "file": "section-5-2-aging-index.html",
                "chart": "aging_index_growth",
            },
            {
                "no": "6.3",
                "title": "생애주기와 재정",
                "file": "section-5-3-lifecycle-fiscal.html",
                "chart": "openfiscal_debt_context",
            },
            {
                "no": "6.4",
                "title": "고령화 사회에서 의료비 지출은 얼마나 빠르게 증가하는가",
                "file": "section-5-3-health-spending-aging.html",
                "chart": "nta_public_health_age_profile",
            },
            {
                "no": "6.5",
                "title": "고령화 예산은 얼마나 증가하는가",
                "file": "section-5-4-aging-budget.html",
                "chart": "openfiscal_aging_budget_trends",
            },
            {
                "no": "6.6",
                "title": "고령층 연금수령액은 얼마나 증가하는가",
                "file": "section-5-5-elderly-pension.html",
                "chart": "elderly_pension_dt_1de8051s",
            },
            {
                "no": "6.7",
                "title": "고령층 연금수령액 구간 분포",
                "file": "section-5-6-elderly-pension-distribution.html",
                "chart": "elderly_pension_amount_distribution",
            },
        ],
    },
    {
        "no": "7",
        "title": "교육과 저출산",
        "file": "chapter-6-education-low-fertility.html",
        "thesis": "교육비와 교육경쟁은 출산 이후에야 나타나는 비용이 아니라, 출산을 결정하기 전부터 부모가 예상하는 장기 위험이다.",
        "sections": [
            {
                "no": "7.1",
                "title": "저출산을 초래할 정도로 교육비가 증가하고 있는가",
                "file": "section-6-1-education-cost-fertility.html",
                "chart": "private_education_cost_trend",
            },
            {
                "no": "7.2",
                "title": "사교육 경쟁은 언제 시작되는가",
                "file": "section-6-2-private-education-by-school-level.html",
                "chart": "private_education_school_level",
            },
            {
                "no": "7.3",
                "title": "교육비 부담은 계층별로 얼마나 다른가",
                "file": "section-6-3-education-cost-inequality.html",
                "chart": "private_education_income_gap",
            },
            {
                "no": "7.4",
                "title": "학생 수가 줄면 교육 부담도 줄어드는가",
                "file": "section-6-4-school-age-decline-education.html",
                "chart": "school_age_private_education_pressure",
            },
            {
                "no": "7.5",
                "title": "부모는 왜 대학까지 책임지려 하는가",
                "file": "section-6-5-education-expectation-burden.html",
                "chart": "education_burden_perception",
            },
        ],
    },
    {
        "no": "8",
        "title": "그래서 어떤 저출산·고령화 정책이 필요한가",
        "file": "chapter-7-policy-recommendations.html",
        "thesis": "저출산·고령화 정책은 출산율과 노동력 확보를 넘어 삶의 질, 가치, 미래에 대한 신뢰를 회복하는 사회정책이어야 한다.",
        "sections": [],
    },
]


CHAPTER_NARRATIVE = {
    "chapter-0.html": [
        "한국의 저출산과 고령화에 대해서는 이미 많은 보고서와 대책이 나와 있다. 문제의식도 낯설지 않다. 청년은 결혼과 출산을 미루고, 부모는 돌봄과 교육비에 눌리고, 여성은 경력단절을 걱정하며, 고령층은 더 오래 일해야 하지만 노후소득은 충분하지 않다. 정부 보고서들은 이 문제를 일자리, 주거, 돌봄, 일가정양립, 연금, 의료, 지역소멸, 재정의 문제로 나누어 설명한다.",
        "그러나 많은 정책 진단은 중요한 문제를 지적하면서도 마지막에는 너무 익숙한 문장으로 돌아간다. 종합적 대응이 필요하다, 부처 간 협력이 중요하다, 생애주기별 지원을 강화해야 한다, 지역 맞춤형 정책이 필요하다는 식이다. 틀린 말은 아니다. 하지만 그런 문장만으로는 무엇이 실제로 작동했고, 무엇이 실패했으며, 어떤 정책이 누구에게 도달하지 못했는지를 알기 어렵다.",
        "이 책을 쓴 이유는 바로 그 지점에 있다. 저출산과 고령화는 선언으로 이해할 수 있는 문제가 아니다. 합계출산율이 낮다는 사실만으로는 충분하지 않고, 예산이 늘었다는 사실만으로도 충분하지 않다. 아이가 태어난 지역에 네 해 뒤에도 남아 있는지, 출산장려금을 많이 주는 지역에서 실제 정주 조건이 개선되는지, 어린이집과 돌봄서비스가 부모의 노동시간과 맞는지, 육아휴직은 제도상 권리가 아니라 현실의 선택지가 되었는지, 고령층 취업 증가는 안정된 노동인지 생계형 노동인지 물어야 한다.",
        "그래서 이 책은 정책 구호보다 점검을 앞세운다. 정부와 연구기관의 보고서를 존중하되, 그 결론을 그대로 반복하지 않는다. KOSIS, ECOS, e-나라지표, 열린재정, 저출산고령사회위원회 발간자료에서 데이터를 모아 같은 질문을 다시 던진다. 출산율이 아니라 출생아 수와 코호트 잔존을 보고, 전국 평균이 아니라 시군구 차이를 보고, 예산 총액이 아니라 사업 수와 세부사업의 방향을 본다.",
        "이 책의 목적은 냉소가 아니다. 정책을 비판하기 위해 비판하는 것도 아니다. 오히려 필요한 정책을 더 분명하게 가려내기 위해서다. 추상적인 정책 제안은 누구도 반대하기 어렵지만, 그만큼 책임도 흐려진다. 데이터로 보면 질문이 구체화된다. 어느 연령대가 줄었는가, 어느 지역에서 빠져나갔는가, 어떤 사업의 돈이 늘었는가, 어떤 계층은 제도 밖에 남았는가. 이런 질문이 있어야 정책의 성공과 실패를 말할 수 있다.",
        "따라서 이 책은 한국의 인구문제를 하나의 숫자로 설명하지 않는다. 출산율은 청년의 삶, 가족 형성, 돌봄, 노동시장, 주거, 지역, 재정이 한꺼번에 압축된 결과다. 고령화율 역시 노인이 많아졌다는 통계가 아니라 누가 일하고, 누가 돌보고, 누가 비용을 부담하며, 어떤 제도가 오래 버틸 수 있는지를 묻는 신호다. 이 책은 그 신호를 가능한 한 차갑게 읽고, 그 위에서 더 현실적인 정책 논의를 시작하려 한다.",
    ],
    "chapter-1.html": [
        "이 장은 숫자를 신뢰하기 전에 숫자가 만들어지는 방식을 묻는다. 인구피라미드, 주민등록인구, 연앙인구, 인구총조사는 모두 한국 사회의 변화를 보여주지만, 같은 현실을 같은 방식으로 재현하지는 않는다.",
        "따라서 첫 장의 목표는 결론을 서두르지 않는 것이다. 어떤 지표를 선택했는지 밝히고, 그 지표가 보이는 것과 가리는 것을 구분해야 이후 출산, 이동, 고령화, 재정의 논의가 흔들리지 않는다.",
    ],
    "chapter-2-population-decline.html": [
        "인구 감소는 전국 총량의 문제처럼 보이지만, 실제 정책은 공간 위에서 작동한다. 같은 시기에도 어떤 지역은 주거지와 산업단지가 확장되며 빠르게 늘고, 어떤 지역은 원도심 쇠퇴와 청년 유출을 동시에 겪는다.",
        "따라서 이 장은 먼저 질문을 바꾼다. 한국 인구가 줄어든다는 말이 곧 모든 지자체가 줄어든다는 뜻인가. 지난 20년 동안 시군구별 인구 변화 속도를 추정하면, 인구감소의 실체는 균일한 하락이 아니라 매우 불균등한 재배치라는 점이 드러난다.",
        "그리고 전체 인구 변화만으로는 충분하지 않다. 고령층 인구 증가는 복지·의료·돌봄 부담의 공간적 압력을 보여 주고, 15-64세 생산연령인구 변화는 지역의 노동공급과 세원 기반을 보여 준다. 두 질문을 분리해서 보아야 같은 인구 증가도 전혀 다른 정책 의미를 갖는다는 점을 확인할 수 있다.",
    ],
    "chapter-2.html": [
        "저출산 정책은 흔히 합계출산율의 반등 여부로 평가된다. 그러나 정책의 목표가 한국 사회의 지속 가능성이라면 먼저 정책이 무엇을 겨냥하는지 구분해야 한다. 현금지원, 돌봄서비스, 육아휴직, 주거지원, 난임지원, 지역정책은 모두 저출산 대책이라는 이름으로 묶이지만 작동 방식과 점검 기준은 서로 다르다.",
        "이 장은 정책 수단의 지도를 먼저 그린 뒤 지역 사례로 내려간다. 특정 지역의 높은 출산율을 성공으로 단정하지 않고, 출생 이후의 코호트 잔존과 정주 조건을 확인함으로써 한국 저출산 정책의 평가 기준을 다시 세운다.",
    ],
    "chapter-3.html": [
        "출생만으로 지역 인구를 설명할 수 없다. 청년이 빠져나가고, 외국인이 들어오고, 다문화 가족이 형성되는 과정에서 지역의 연령구조와 가족구조는 다시 쓰인다.",
        "이 장은 전국 평균을 벗어나 시군구의 차이를 본다. 고령화율, 청년 이동, 외국인 유입, 다문화 출생을 함께 놓으면 인구감소는 단순한 수량 변화가 아니라 공간 구조의 변화로 읽힌다.",
    ],
    "chapter-4.html": [
        "출산은 개인의 의지만으로 설명되지 않는다. 혼인할 수 있는 조건, 안정적으로 살 집, 아이를 맡길 수 있는 돌봄, 일을 계속할 수 있는 제도가 함께 있을 때 가족 형성은 현실적인 선택지가 된다.",
        "이 장은 가족 형성을 둘러싼 생활 조건을 다룬다. 혼인과 출생의 관계를 확인하되, 그 관계를 떠받치는 주거, 돌봄, 일가정양립, 가구 변화까지 함께 읽는다.",
    ],
    "chapter-5.html": [
        "저출산과 고령화의 마지막 질문은 부담의 배분이다. 누가 일하고, 누가 돌보고, 누가 세금을 내고, 누가 공공서비스를 필요로 하는가가 인구구조 변화와 함께 달라진다.",
        "이 장은 청년 노동공급의 축소, 고령층 경제활동의 증가, 생애주기 재정 부담을 하나의 흐름으로 묶는다. 인구문제는 결국 세대 간 이전과 사회적 비용의 재구성 문제로 귀결된다.",
    ],
    "chapter-6-education-low-fertility.html": [
        "교육은 한국 저출산 논의에서 늘 등장하지만, 자주 ‘교육비가 부담이다’라는 문장 하나로 지나간다. 그러나 교육비는 단순한 지출 항목이 아니다. 부모가 아이를 낳기 전에 이미 예상하는 장기 비용이고, 자녀 수를 줄이는 방식으로 관리하려는 위험이며, 계층 이동의 가능성과 불안을 동시에 담고 있는 사회적 압력이다.",
        "이 장은 교육비를 출산 이후의 사후 부담이 아니라 출산 이전의 기대 비용으로 읽는다. 사교육비 총액과 1인당 월평균 비용, 참여율, 학교급별 차이, 소득계층별 격차, 부모의 대학 교육 기대를 함께 보면 한국의 교육경쟁이 왜 가족 형성의 조건을 좁히는지 더 선명해진다.",
    ],
}


CHART_META = {
    "age_composition_projection": {
        "title": "전국 연령구성비 전망",
        "kind": "line",
        "csv": "age_composition_projection.csv",
        "source": "KOSIS DT_1BPB002 주요 인구지표(성비·인구성장률·인구구조·부양비 등)/시도, 중위추계",
        "note": "유소년층 비중은 낮아지고 65세 이상 비중은 장기적으로 급상승한다.",
    },
    "population_pyramid_four_panel": {
        "title": "성·연령별 인구피라미드: 1980, 1990, 2020, 2025",
        "kind": "pyramid",
        "csv": "population_pyramid_5yr_1980_1990_2020_2025.csv",
        "source": "KOSIS DT_1BPA001 성 및 연령별 추계인구(1세별·5세별) / 전국, 중위추계",
        "note": "KOSIS의 중위추계 5세 연령군을 사용했다. 역사 시계열의 공통성을 위해 최상위 구간은 80세 이상으로 통일했으며, 네 패널은 같은 축 범위를 사용한다.",
    },
    "sex_ratio_projection": {
        "title": "전국 성비와 인구성장률",
        "kind": "line",
        "csv": "sex_ratio_projection.csv",
        "source": "KOSIS DT_1BPB002 주요 인구지표, 중위추계",
        "note": "성비와 성장률은 인구 기준을 읽을 때 함께 확인해야 하는 배경 지표다.",
    },
    "population_measure_comparison": {
        "title": "주민등록인구·인구총조사·장래인구추계의 차이",
        "kind": "line",
        "csv": "population_measure_comparison.csv",
        "source": "KOSIS DT_1B040A3 주민등록인구현황(전국, 12월), INH_1IN1503_01 인구총조사 인구(전국), DT_1BPB002 장래인구추계 중위추계, 통계청 2000·2005·2010 인구주택총조사 전수집계 결과",
        "note": "2000년부터 비교한다. 인구총조사는 2000·2005·2010년 전수조사 값과 2015년 이후 등록센서스 연간 값을 연결했으며, 중간 연도는 조사값이 없으므로 비워 두었다.",
    },
    "population_measure_gap": {
        "title": "인구 측정 기준별 차이(주민등록인구 대비)",
        "kind": "line",
        "csv": "population_measure_gap.csv",
        "source": "KOSIS DT_1B040A3, INH_1IN1503_01, DT_1BPB002와 통계청 2000·2005·2010 인구주택총조사 결과를 이용해 차이 계산",
        "note": "절대 인구 규모가 비슷해 보일 때는 기준 간 차이를 따로 그려야 외국인 포함, 국내 상주 기준, 추계 기준의 효과가 드러난다. 총조사 차이는 조사값이 있는 연도만 해석한다.",
    },
    "resident_registration_2010_jump": {
        "title": "주민등록인구의 2010년 단절: 전년 대비 증가분",
        "kind": "bar",
        "csv": "resident_registration_2010_jump.csv",
        "source": "KOSIS DT_1B040A3 주민등록인구현황(전국, 12월); 행정안전부 주민등록 인구통계 작성기준 변경 보도자료(2010.1.29, 2010.9.20)",
        "note": "2009년 10월 거주불명등록 제도 시행과 2010년 거주불명등록자 통계 포함은 주민등록인구 장기 시계열에 단절을 만든다. 2010년 증가는 자연증가나 이동만으로 해석할 수 없다.",
    },
    "resident_registration_centenarian_trend": {
        "title": "100세 이상 주민등록인구 추세",
        "kind": "line",
        "csv": "resident_registration_centenarian_trend.csv",
        "source": "KOSIS DT_1B04006 행정구역(시군구)별/1세별 주민등록인구, 전국, 전체 성별, 2008-2025",
        "note": "100세 이상 인구는 장수 증가뿐 아니라 장기 거주불명자 조사와 주민등록 말소·정리 방식에 민감하다. 2021년 급감은 통계가 생물학적 고령화만을 반영하지 않는다는 점을 보여준다.",
    },
    "sigungu_population_slope_map": {
        "title": "시군구 인구 변화 속도: 연도 회귀계수(2004-2024)",
        "kind": "map",
        "csv": "sigungu_population_trend_map_values.csv",
        "source": "KOSIS DT_1B040A3 행정구역(시군구)별 성별 주민등록인구수, 2004-2024; 행정구역 경계는 2018년 시군구 TopoJSON",
        "note": "각 시군구별로 주민등록인구를 종속변수, 연도를 독립변수로 한 단순회귀의 연도 계수다. 붉은색은 증가, 푸른색은 감소를 뜻하며 색이 진할수록 연평균 변화 규모가 크다.",
    },
    "sigungu_older_population_slope_map": {
        "title": "시군구 65세 이상 인구 변화 속도: 연도 회귀계수(2008-2024)",
        "kind": "map",
        "csv": "sigungu_older_population_trend_map_values.csv",
        "source": "KOSIS DT_1B04006 행정구역(시군구)별/1세별 주민등록인구, 2008-2024; 행정구역 경계는 2018년 시군구 TopoJSON",
        "note": "각 시군구의 65세 이상 주민등록인구를 종속변수, 연도를 독립변수로 한 단순회귀의 연도 계수다. 고령층 인구 증가는 복지·의료·돌봄 수요의 공간적 압력을 보여준다.",
    },
    "sigungu_working_age_population_slope_map": {
        "title": "시군구 15-64세 생산연령인구 변화 속도: 연도 회귀계수(2008-2024)",
        "kind": "map",
        "csv": "sigungu_working_age_population_trend_map_values.csv",
        "source": "KOSIS DT_1B04006 행정구역(시군구)별/1세별 주민등록인구, 2008-2024; 행정구역 경계는 2018년 시군구 TopoJSON",
        "note": "각 시군구의 15-64세 주민등록인구를 종속변수, 연도를 독립변수로 한 단순회귀의 연도 계수다. 생산연령인구 증가는 지역 노동공급과 소비 기반의 확장 여부를 보여준다.",
    },
    "sigungu_population_concentration": {
        "title": "시군구 인구 집중도: 상위 지역·수도권·성장거점 비중",
        "kind": "line",
        "csv": "sigungu_population_concentration.csv",
        "source": "KOSIS DT_1B040A3 행정구역(시군구)별 성별 주민등록인구수, 2004-2024",
        "note": "행정구역 중복을 줄이기 위해 구가 별도로 집계되는 도시는 하위 구를 사용하고, 출장소처럼 인구가 0인 보조 행정단위는 제외했다. 성장거점 20개는 2024년 기준 하위 행정단위 중 2004-2024년 회귀계수가 큰 지역이다.",
    },
    "sigungu_population_concentration_indices": {
        "title": "시군구 인구 분포 지표: 지니계수·HHI·유효 지역 수",
        "kind": "line",
        "csv": "sigungu_population_concentration_indices.csv",
        "source": "KOSIS DT_1B040A3 행정구역(시군구)별 성별 주민등록인구수, 2004-2024",
        "note": "지니계수와 HHI가 높아질수록 인구가 소수 지역에 더 몰린다. 유효 지역 수는 1/HHI 형태의 직관적 환산값으로 낮아질수록 집중이 강해진다.",
    },
    "low_fertility_policy_typology": {
        "title": "저출산 정책수단의 작동 논리와 평가 질문",
        "kind": "taxonomy",
        "csv": "low_fertility_policy_typology.csv",
        "source": "저출산고령사회위원회·보건복지부 저출생 대책 자료, 고용노동부 모성보호·육아지원 제도, 국토교통부 신혼·출산가구 주거지원 정책을 분류",
        "note": "정책을 예산 항목이 아니라 작동 경로별로 나눈 분류다. 이후 장의 분석은 각 수단이 출생, 정주, 돌봄 접근성, 부모의 시간, 주거 안정 중 무엇을 바꾸었는지를 점검한다.",
    },
    "low_fertility_budget_trend": {
        "title": "저출생 대응 예산 규모: 광의·협의 기준 비교",
        "kind": "line",
        "csv": "low_fertility_budget_trend.csv",
        "source": "국회예산정책처 2026년도 예산안 총괄 분석 IV, 저출산고령사회위원회 제출자료 재인용",
        "note": "광의의 저출생 예산은 시행계획 기준의 넓은 저출생 대응 예산이고, 협의의 저출생 예산은 저출생과 직접 연결되는 사업을 재분류한 값이다. 2026년 시행계획 기준 총액은 아직 별도 확정 공표 전이므로 2025년까지 제시했다.",
    },
    "low_fertility_major_budget_2026": {
        "title": "2026년 예산안 기준 저출생 대응 주요사업 분야별 규모",
        "kind": "bar",
        "csv": "low_fertility_major_budget_2026.csv",
        "source": "국회예산정책처 2026년도 예산안 총괄 분석 IV, 기획재정부 제출자료 재구성",
        "note": "2026년 시행계획 기준 전체 저출생 대응 예산이 아니라, 예산안에서 확인되는 주요 사업을 일·가정양립, 양육·돌봄, 주거 분야로 재분류한 부분집합이다.",
    },
    "pronatalist_policy_country_comparison": {
        "title": "저출산 정책 강도와 출산율 변화: 한국·싱가포르·헝가리·일본",
        "kind": "bar",
        "csv": "pronatalist_policy_country_comparison.csv",
        "source": "World Bank Fertility Rate, KOSTAT 2024 출생·사망통계 잠정결과, SingStat Births and Fertility, Hungary KSH STADAT, Eurostat demo_find, 일본 후생노동성 2024 인구동태통계, 각국 공식 정책자료 재구성",
        "note": "각국의 대표적 저출산 정책을 현금·세제, 주거, 돌봄·휴직, 구조개혁 성격으로 요약하고, 정책 강화 이후 합계출산율의 시작점·정점·최근값을 비교했다. 값은 국가별 최신 공표 기준이 달라 추세 판단용으로 읽어야 한다.",
    },
    "housing_support_policy_budget": {
        "title": "저출생 대응 주요사업 중 주거 분야 예산",
        "kind": "bar",
        "csv": "housing_support_policy_budget.csv",
        "source": "국회예산정책처 2026년도 예산안 총괄 분석 IV, 저출생 대응 주요사업 표 재구성",
        "note": "2026년 예산안 주요사업 기준 주거 분야는 신혼부부형 매입임대·전세임대·통합공공임대 등을 중심으로 크게 늘어난다. 전체 저출생 예산이 아니라 주요사업 부분집합이다.",
    },
    "housing_security_outcomes_national": {
        "title": "전국 40세 미만 주거 안정성과 혼인·출생 지표",
        "kind": "line",
        "csv": "housing_security_outcomes_national.csv",
        "source": "KOSIS DT_1OH0403·DT_1OH0418 주택소유통계, DT_1B8000I 시군구/인구동태건수 및 동태율",
        "note": "40세 미만 가구주 가구의 주택보유율과 전국 조혼인율·조출생률을 같은 시간축에 놓았다. 주거지원 수혜 효과가 아니라 주거 안정성과 가족 형성 조건의 동행 여부를 보는 점검이다.",
    },
    "capital_region_housing_marriage_birth": {
        "title": "수도권 주거 안정성과 혼인·출생 지표",
        "kind": "line",
        "csv": "capital_region_housing_marriage_birth.csv",
        "source": "KOSIS DT_1OH0403·DT_1OH0418 주택소유통계, DT_1B8000I 시군구/인구동태건수 및 동태율",
        "note": "서울·인천·경기의 40세 미만 가구주 주택보유율과 조혼인율·조출생률을 비교한다. 수도권 안에서도 서울과 경기의 주거·가족 형성 조건은 다르게 움직인다.",
    },
    "housing_security_outcome_regression": {
        "title": "주거 안정성과 혼인·출생의 지역-연도 회귀계수",
        "kind": "bar",
        "csv": "housing_security_outcome_regression.csv",
        "source": "KOSIS DT_1OH0403·DT_1OH0418, DT_1B8000I를 이용한 시도-연도 패널 회귀",
        "note": "결과변수는 조혼인율과 조출생률이며, 설명변수는 40세 미만 가구주 주택보유율과 연도 추세다. 개인별 수혜자료가 아니므로 인과효과가 아니라 구조적 동행 여부로 읽어야 한다.",
    },
    "housing_tenure_young_newlywed": {
        "title": "30대 이하·신혼·미혼 가구의 점유형태",
        "kind": "line",
        "csv": "housing_tenure_young_newlywed.csv",
        "source": "주택금융공사 주택금융 및 보금자리론 실태조사 DT_KHFC_026 점유형태",
        "note": "공공주택 지원은 자가 진입만이 아니라 전세·월세 중심의 불안정한 초기 주거 경로를 얼마나 안정시키는지를 보아야 한다.",
    },
    "housing_finance_burden_by_age": {
        "title": "29세 이하·30대 가구주의 부채와 원리금 상환 부담",
        "kind": "line",
        "csv": "housing_finance_burden_by_age.csv",
        "source": "KOSIS DT_1HDAAA06 가구주연령계층별 자산·부채·소득 현황",
        "note": "전세·구입자금 대출은 초기 진입장벽을 낮추지만, 이미 높은 부채와 상환 부담 위에 얹힐 경우 출산 위험을 줄이기보다 미래 부담을 뒤로 미룰 수 있다.",
    },
    "youth_housing_consumption_pressure": {
        "title": "가계소비 중 주거비 비중",
        "kind": "line",
        "csv": "youth_housing_consumption_pressure.csv",
        "source": "청년 프로젝트 보조 정리자료, 가계소비 중 주거비 비중",
        "note": "청년·신혼부부 주거지원은 혼인·출산 지표만이 아니라 일상 소비에서 주거비 압력이 완화되는지로도 평가해야 한다.",
    },
    "international_housing_fertility_cases": {
        "title": "주거지원·주거비와 출산율의 국제 사례",
        "kind": "bar",
        "csv": "international_housing_fertility_cases.csv",
        "source": "KOSIS 합계출산율, SingStat Births and Fertility 2024, INSEE Demographic Report 2024, Israel CBS Statistical Abstract 2023, Singapore gov.sg·HDB, OECD Affordable Housing Database",
        "note": "싱가포르는 강한 공공주택 체계에도 합계출산율이 1명 미만이고, 이스라엘은 집값 상승 압력이 커도 높은 출산율을 보인다. 주거지원은 단독 처방이 아니라 돌봄·노동·생활권 안정과 결합될 때 인구 효과를 기대할 수 있다.",
    },
    "private_education_cost_trend": {
        "title": "초중고 사교육비 총액·1인당 월평균 사교육비·참여율",
        "kind": "line",
        "csv": "private_education_cost_trend.csv",
        "source": "KOSIS DT_1PE003 학교급별 사교육비 총액, DT_1PE201 학교급별 학생 1인당 월평균 사교육비, DT_1PE301 학교급별 사교육 참여율, 국가데이터처·교육부 초중고사교육비조사",
        "note": "사교육비 총액은 억원 단위를 조원으로 환산했고, 1인당 월평균 사교육비는 전체학생 기준 만원이다. 2017년부터 진로·진학 학습상담 비용이 포함되며 2017년 자료가 소급 보정되었다.",
    },
    "private_education_school_level": {
        "title": "학교급별 사교육비와 참여율",
        "kind": "line",
        "csv": "private_education_school_level.csv",
        "source": "KOSIS DT_1PE201, DT_1PE301, 국가데이터처·교육부 초중고사교육비조사",
        "note": "초등학교·중학교·고등학교의 전체학생 기준 월평균 사교육비와 참여율을 함께 제시한다. 사교육 경쟁이 입시 직전의 문제가 아니라 초등 단계부터 시작되는지를 확인하기 위한 그림이다.",
    },
    "high_school_private_education_drivers": {
        "title": "고등학생 사교육 참여율을 끌어올린 과목과 유형",
        "kind": "line",
        "csv": "high_school_private_education_drivers.csv",
        "source": "KOSIS DT_1PE301 학교급별 사교육 참여율, 국가데이터처·교육부 초중고사교육비조사",
        "note": "고등학교만 분리해 전체 참여율과 일반교과, 주요 과목, 온라인 강좌, 진로·진학 학습상담 참여율을 비교했다. 2020년 코로나19 시기 이후 2024년까지의 상승과 2025년의 하락을 구분해서 읽어야 한다.",
    },
    "private_education_income_gap": {
        "title": "가구소득별 사교육비와 참여율 격차",
        "kind": "bar",
        "csv": "private_education_income_gap.csv",
        "source": "KOSIS DT_1PE209 가구 월평균 소득별 학생 1인당 월평균 사교육비, DT_1PE309 가구 월평균 소득별 사교육 참여율",
        "note": "2025년 기준 소득구간별 전체학생 1인당 월평균 사교육비와 참여율이다. 고소득 구간은 800만원 이상을 800-1,000만원 미만과 1,000만원 이상으로 나누어 읽을 수 있다.",
    },
    "newlywed_income_fertility": {
        "title": "초혼 신혼부부 소득구간별 자녀 보유와 평균 출생아 수",
        "kind": "bar",
        "csv": "newlywed_income_fertility.csv",
        "source": "KOSIS DT_1NW2016 초혼 신혼부부의 소득(근로·사업소득) 구간별 출산자녀 현황",
        "note": "소득은 부부의 연간 근로·사업소득 구간이다. 신혼부부 통계는 혼인신고 후 5년이 지나지 않은 부부를 대상으로 하므로, 전체 생애 출산율이 아니라 결혼 초기의 자녀 보유와 출산 속도를 보여준다.",
    },
    "youth_employment_context": {
        "title": "청년 고용 기반의 변화(2000=100)",
        "kind": "line",
        "csv": "youth_employment_context.csv",
        "source": "e-나라지표 149501 청년 고용동향, 국가데이터처 경제활동인구조사",
        "note": "15-29세 청년층의 생산가능인구, 경제활동인구, 취업자를 2000년=100으로 지수화했다. 출산의 직접 원인이라기보다 혼인과 첫 출산을 미루게 하는 노동시장 배경으로 읽어야 한다.",
    },
    "school_age_private_education_pressure": {
        "title": "학생 수 감소와 사교육비 압력",
        "kind": "line",
        "csv": "school_age_private_education_pressure.csv",
        "source": "KOSIS DT_1BPB002 장래인구추계 0-14세·15-64세 구성비와 총인구, DT_1PE003, DT_1PE201, DT_1PE301",
        "note": "2007년을 100으로 한 지수다. 학생 수가 줄어도 1인당 사교육비와 참여율이 자동으로 낮아지는지 확인하기 위해 같은 축에 놓았다.",
    },
    "education_burden_perception": {
        "title": "자녀 교육비 부담 인식과 부담 항목",
        "kind": "line",
        "csv": "education_burden_perception.csv",
        "source": "KOSIS DT_1SSED100R 자녀 교육비 부담 인식, DT_1SSED110R 가장 부담되는 자녀 교육비 항목, 통계청 사회조사",
        "note": "전국 30세 이상 가구주 중 학생 자녀가 있는 가구의 교육비 부담 인식과 부담 항목 분포다. 사회조사는 2년 주기 조사이므로 격년으로 나타난다.",
    },
    "yeonggwang_cohort": {
        "title": "지역 사례: 출생 코호트 잔존",
        "kind": "barLine",
        "csv": "yeonggwang_birth_cohort_summary.csv",
        "source": "KOSIS DT_1B04006 행정구역(시군구)별/1세별 주민등록인구, 영광군 필터",
        "note": "높은 출산율이 곧 지역 내 유아 인구 유지로 이어지는 것은 아니다.",
    },
    "birth_incentive_region_retention": {
        "title": "출산장려금 적극 지역: 조출생률과 0세→4세 코호트 잔존율",
        "kind": "panel",
        "csv": "birth_incentive_region_panel_cbr_retention.csv",
        "source": "KOSIS DT_1B8000I 시군구/인구동태건수 및 동태율, DT_1B04006 행정구역(시군구)별/1세별 주민등록인구",
        "note": "왼쪽은 출생연도 기준 조출생률(해당 연도 출생아 수/전체 인구×1,000), 오른쪽은 같은 출생연도 0세 인구가 4년 뒤 4세 인구로 얼마나 남았는지를 보여준다.",
    },
    "birth_incentive_region_summary": {
        "title": "2013-2020년 출생 코호트 평균 잔존율",
        "kind": "bar",
        "csv": "birth_incentive_region_cohort_summary.csv",
        "source": "KOSIS DT_1B04006 행정구역(시군구)별/1세별 주민등록인구, 2013-2024년",
        "note": "8개 출생 코호트의 평균 잔존율을 비교하면 현금성 지원이 출생 이후 정주 유지로 이어졌는지 점검할 수 있다.",
    },
    "fertility_comparison": {
        "title": "영광군과 전국 합계출산율 비교",
        "kind": "line",
        "csv": "fertility_comparison.csv",
        "source": "KOSIS 인구동태 합계출산율. 영광군 값은 원본 프로젝트의 KOSIS 수집 결과를 재구성",
        "note": "지역 출산율은 전국보다 높을 수 있지만, 실제 코호트 잔존과 함께 읽어야 한다.",
    },
    "international_tfr_asia": {
        "title": "아시아 주요국 합계출산율 추세",
        "kind": "line",
        "csv": "international_tfr_trends.csv",
        "source": "World Bank SP.DYN.TFRT.IN; Taiwan Gender Indicators, Ministry of the Interior administrative data",
        "note": "한국·일본·싱가포르는 World Bank, 대만은 공식 성별지표 플랫폼의 총생육률을 1,000분율에서 여성 1명당 출생아 수로 환산했다.",
    },
    "international_tfr_europe": {
        "title": "유럽 주요국 합계출산율 추세",
        "kind": "line",
        "csv": "international_tfr_trends.csv",
        "source": "World Bank SP.DYN.TFRT.IN",
        "note": "프랑스, 스웨덴, 독일, 이탈리아, 스페인, 영국의 합계출산율 추세다. 유럽도 대체수준 2.1에는 크게 못 미친다.",
    },
    "fertility_family_structure_comparison": {
        "title": "출산율, 비혼 출산, 이민자 출산의 국제 비교",
        "kind": "mixed",
        "csv": "fertility_family_structure_comparison.csv",
        "source": "World Bank SP.DYN.TFRT.IN; OECD Family Database/Our World in Data; Eurostat DEMO_FACBC",
        "note": "합계출산율은 2024년 또는 최신값, 비혼 출산 비중은 OECD Family Database를 가공한 Our World in Data의 최신값, 외국 출생 모친 출생 비중은 Eurostat 2023년 자료다. 지표 연도가 서로 다르므로 구조 비교용으로 읽어야 한다.",
    },
    "sigungu_aging_top": {
        "title": "2024년 고령화율 상위 시군구",
        "kind": "bar",
        "csv": "sigungu_aging_top.csv",
        "source": "KOSIS DT_1B04006 행정구역(시군구)별/1세별 주민등록인구, 2024년 총인구 항목 집계",
        "note": "전국 평균은 시군구별 고령화 속도 차이를 가린다.",
    },
    "youth_population_enara": {
        "title": "청년 생산가능인구 추세",
        "kind": "line",
        "csv": "youth_population_enara.csv",
        "source": "e-나라지표 149501 청년 고용동향, 국가데이터처 경제활동인구조사",
        "note": "청년층 기반의 축소는 지역 이동, 혼인, 출산, 노동공급 문제와 연결된다.",
    },
    "elderly_labor_dt_1de8031s": {
        "title": "고령층 고용현황: 연령별 경제활동상태",
        "kind": "panel",
        "csv": "elderly_labor_dt_1de8031s_trends.csv",
        "source": "KOSIS DT_1DE8031S 경제활동인구조사 고령층 부가조사, 매년 5월",
        "note": "55~79세 전체, 55~64세, 65~79세를 나누어 고령층인구, 경제활동인구, 취업자, 고용률, 실업자, 실업률, 비경제활동인구의 추세를 함께 본다.",
    },
    "elderly_labor_dt_1de8031s_summary": {
        "title": "고령층 고용현황 요약: 2010년과 2025년",
        "kind": "bar",
        "csv": "elderly_labor_dt_1de8031s_summary.csv",
        "source": "KOSIS DT_1DE8031S 경제활동인구조사 고령층 부가조사, 매년 5월",
        "note": "2010년과 2025년을 비교해 고령층 노동시장 확대가 인구 증가, 참여 증가, 비경제활동 규모 증가를 동시에 포함한다는 점을 확인한다.",
    },
    "elderly_activity_life_course_indicators": {
        "title": "고령층 경제활동 부가조사: 일자리 이탈과 장래 근로 의향",
        "kind": "line",
        "csv": "elderly_activity_life_course_indicators.csv",
        "source": "KOSIS DT_1DE8035S, DT_1DE8036S, DT_1DE8038S, DT_1DE8042S, DT_1DE8044S, DT_1DE8057S 경제활동인구조사 고령층 부가조사, 매년 5월",
        "note": "55~79세의 주된 일자리 이탈, 구직 경험, 취업 경험, 장래 근로 희망, 희망 근로연령을 연결해 고령층 경제활동을 생애경로 관점에서 읽는다.",
    },
    "elderly_activity_exit_reasons_2025": {
        "title": "2025년 고령층이 주된 일자리를 그만둔 이유",
        "kind": "bar",
        "csv": "elderly_activity_exit_reasons_2025.csv",
        "source": "KOSIS DT_1DE8037S 성별 가장 오래 근무한 일자리를 그만둔 이유, 2025년 5월",
        "note": "55~79세 중 가장 오래 근무한 일자리를 그만둔 사람을 분모로 각 이유의 비중을 계산했다.",
    },
    "elderly_activity_future_work_reasons_2025": {
        "title": "2025년 고령층이 앞으로도 일하려는 이유",
        "kind": "bar",
        "csv": "elderly_activity_future_work_reasons_2025.csv",
        "source": "KOSIS DT_1DE8044S 성별 장래 근로 희망의사 및 근로 희망사유, 2025년 5월",
        "note": "55~79세 장래 근로 희망자를 분모로 근로 희망 이유의 비중을 계산했다.",
    },
    "elderly_activity_job_preferences_2025": {
        "title": "2025년 고령층이 원하는 일자리 조건",
        "kind": "bar",
        "csv": "elderly_activity_job_preferences_2025.csv",
        "source": "KOSIS DT_1DE8046S, DT_1DE8048S, DT_1DE8050S 경제활동인구조사 고령층 부가조사, 2025년 5월",
        "note": "장래 근로 희망자를 분모로 일자리 선택기준, 희망 일자리 형태, 희망 임금수준을 비교했다.",
    },
    "elderly_employment_structure_2025": {
        "title": "2025년 고령층 취업자의 산업·직업 분포",
        "kind": "bar",
        "csv": "elderly_employment_structure_2025.csv",
        "source": "KOSIS DT_1DE8061_11 연령/산업별 취업분포, DT_1DE8063_8 연령/직업별 취업분포, 2025년 5월",
        "note": "55~79세 취업자가 어느 산업과 직업에 집중되어 있는지, 전체 고령층 취업자 중 해당 범주의 비중으로 계산했다.",
    },
    "elderly_regional_labor_60plus_slopes": {
        "title": "시도별 60세 이상 노동시장 변화 속도",
        "kind": "panel",
        "csv": "elderly_regional_labor_60plus_slopes.csv",
        "source": "KOSIS DT_1DA7015S 행정구역(시도)/연령별 경제활동인구, DT_1DA7031S 취업자, DT_1DA7095S 실업자, 2010-2025년",
        "note": "각 시도에서 연도를 독립변수로 두고 60세 이상 취업자, 고용률, 실업자, 비경제활동인구를 각각 회귀분석해 연평균 변화 속도를 비교한다.",
    },
    "nta_public_health_age_profile": {
        "title": "연령별 1인 공공보건소비: 국민이전계정",
        "kind": "line",
        "csv": "nta_public_health_age_profile.csv",
        "source": "KOSIS DT_1NTA2003 생애주기적자계정(1인규모), 세부계정 공공보건소비",
        "note": "공공보건소비는 국민이전계정의 1인 규모 금액(천원)이다. 원 요청의 DT_1NTA03은 현재 KOSIS에서 DT_1NTA2003으로 제공되는 표와 대응되는 최신 표로 확인했다.",
    },
    "nta_public_health_age_group_trend": {
        "title": "연령대별 1인 공공보건소비 증가 속도",
        "kind": "line",
        "csv": "nta_public_health_age_group_trend.csv",
        "source": "KOSIS DT_1NTA2003 생애주기적자계정(1인규모), 세부계정 공공보건소비",
        "note": "각 연령대의 각세별 1인 공공보건소비를 단순 평균한 값이다. 인구가중 총액이 아니라 나이별 지출 프로필의 변화 속도를 읽기 위한 보조 지표다.",
    },
    "elderly_pension_dt_1de8051s": {
        "title": "고령층 연금수령액과 연금수령률",
        "kind": "line",
        "csv": "elderly_pension_dt_1de8051s_trends.csv",
        "source": "KOSIS DT_1DE8051S 경제활동인구조사 고령층 부가조사, 성별 연금수령여부 및 월평균수령액, 매년 5월",
        "note": "55~79세를 대상으로 성별 평균 연금수령액(만원)과 연금수령자 비율을 계산했다. 연금수령률은 연금수령자/55~79세 인구×100이다.",
    },
    "elderly_pension_amount_distribution": {
        "title": "고령층 연금수령액 구간 분포",
        "kind": "bar",
        "csv": "elderly_pension_dt_1de8051s_distribution.csv",
        "source": "KOSIS DT_1DE8051S 경제활동인구조사 고령층 부가조사, 성별 연금수령여부 및 월평균수령액, 매년 5월",
        "note": "연금수령자 중 월평균 수령액 구간별 비중을 계산했다. 2008년에는 25만원 미만 비중이 컸지만, 2025년에는 25~100만원 구간과 100만원 이상 구간이 크게 늘었다.",
    },
    "multicultural_birth_rate": {
        "title": "전국 다문화 출생 비중",
        "kind": "line",
        "csv": "multicultural_birth_rate.csv",
        "source": "KOSIS DT_1BB0006 지역별 다문화 출생",
        "note": "출생 구조는 내국인 출생만으로 설명되지 않으며, 지역별 다문화 출생 비중은 가족 형성 구조 변화를 보여준다.",
    },
    "childcare_children": {
        "title": "어린이집 보육아동수",
        "kind": "line",
        "csv": "childcare_children.csv",
        "source": "KOSIS DT_15407_NN002 어린이집 보육아동 현황",
        "note": "출생아 수 감소는 보육 수요와 돌봄 인프라의 지속 가능성 문제로 이어진다.",
    },
    "parental_leave_gender_users": {
        "title": "육아휴직급여 수급자 수와 남성 비중",
        "kind": "line",
        "csv": "parental_leave_gender_users.csv",
        "source": "e-나라지표 150401 출산전후휴가 및 육아휴직급여 현황, 고용노동부 고용보험 DB",
        "note": "육아휴직급여 초회수급자 수를 성별로 나누고 남성 비중을 계산했다. 2025년 값은 e-나라지표 제공 최신값이다.",
    },
    "maternity_leave_support": {
        "title": "출산전후휴가급여 수급자와 지원금액",
        "kind": "line",
        "csv": "maternity_leave_support.csv",
        "source": "e-나라지표 150401 출산전후휴가 및 육아휴직급여 현황, 고용노동부 고용보험 DB",
        "note": "출산전후휴가급여 초회수급자 수와 지원금액, 1인당 지원금액을 계산했다. 지원금액 단위는 백만원이며 1인당 금액은 백만원/명이다.",
    },
    "maternity_parental_leave_financing_pressure": {
        "title": "모성보호성 급여 지출 압력: 출산전후휴가급여와 육아휴직급여",
        "kind": "line",
        "csv": "maternity_parental_leave_financing_pressure.csv",
        "source": "e-나라지표 150401 출산전후휴가 및 육아휴직급여 현황, 고용노동부 고용보험 DB",
        "note": "출산전후휴가급여와 육아휴직급여 지원금액을 조원 단위로 환산했다. 두 항목은 고용보험을 기반으로 한 출산·육아기 소득보전 지출의 핵심 항목이다.",
    },
    "parental_leave_per_user_support": {
        "title": "성별 육아휴직급여 초회수급자 기준 환산액",
        "kind": "line",
        "csv": "parental_leave_per_user_support.csv",
        "source": "e-나라지표 150401 출산전후휴가 및 육아휴직급여 현황, 고용노동부 고용보험 DB",
        "note": "육아휴직급여 지원금액을 육아휴직급여 초회수급자 수로 나누어 전체, 여성근로자, 남성근로자의 환산액을 계산했다. 단위는 백만원/초회수급자이며, 개인별 실제 평균 수령액과는 구분해 읽어야 한다.",
    },
    "parental_leave_access_gap_2025": {
        "title": "육아휴직 제도 접근성의 노동시장 격차(2025년 8월 기준)",
        "kind": "bar",
        "csv": "parental_leave_access_gap_2025.csv",
        "source": "국가데이터처 2025년 8월 경제활동인구조사 근로형태별 부가조사 및 비임금근로 부가조사, e-나라지표 150401",
        "note": "정규직·비정규직 규모와 고용보험 가입률, 비임금근로자 규모를 결합한 접근성 점검표다. 전체 노동자를 기준으로 한 근사치이며, 실제 육아휴직 대상 부모 규모와는 다르다.",
    },
    "preschool_childcare_time_by_parent": {
        "title": "미취학 자녀 가구의 부모 돌보기 시간",
        "kind": "line",
        "csv": "preschool_childcare_time_by_parent.csv",
        "source": "통계청, 2024년 생활시간조사 결과(2025.7. 공표), 미취학 자녀 가구 시간사용",
        "note": "미취학 자녀가 있는 가구에서 남편과 아내의 하루 돌보기 시간을 분 단위로 환산하고, 부모 합산 돌보기 시간 중 남편 비중을 계산했다.",
    },
    "dual_earner_child_housework_time": {
        "title": "18세 미만 자녀 맞벌이 가구의 가사노동 시간",
        "kind": "line",
        "csv": "dual_earner_child_housework_time.csv",
        "source": "통계청, 2024년 생활시간조사 결과(2025.7. 공표), 18세 미만 자녀가 있는 맞벌이 가구 시간사용",
        "note": "18세 미만 자녀가 있는 맞벌이 가구에서 남편과 아내의 하루 가사노동 시간을 분 단위로 환산하고, 부모 합산 가사노동 시간 중 남편 비중을 계산했다.",
    },
    "childcare_supply_by_type": {
        "title": "어린이집 유형별 개소 추세",
        "kind": "line",
        "csv": "childcare_supply_by_type.csv",
        "source": "KOSIS DT_15407_NN001 어린이집 설치·운영 현황",
        "note": "어린이집 유형별 개소 수를 비교했다. 민간·가정 어린이집 감소와 국공립·직장 어린이집 확대가 동시에 나타나는지 확인한다.",
    },
    "childcare_users_by_type": {
        "title": "어린이집 유형별 이용 아동 수",
        "kind": "line",
        "csv": "childcare_users_by_type.csv",
        "source": "KOSIS DT_15407_NN002 어린이집 보육아동 현황",
        "note": "KOSIS의 보육아동수는 실제 어린이집을 이용하는 아동 규모로 읽을 수 있다. 출생아 감소 이후 어떤 유형의 보육 수요가 더 빠르게 줄었는지 확인한다.",
    },
    "childcare_supply_users_by_type": {
        "title": "어린이집 유형별 개소·이용 아동 결합표",
        "kind": "table",
        "csv": "childcare_supply_users_by_type.csv",
        "source": "KOSIS DT_15407_NN001 어린이집 설치·운영 현황, DT_15407_NN002 어린이집 보육아동 현황",
        "note": "연도와 어린이집 유형을 기준으로 시설 수, 보육아동수, 시설당 아동수, 유형별 비중을 결합했다. 그림의 CSV 다운로드용 원자료다.",
    },
    "childcare_time_flexible_facilities": {
        "title": "필요한 시간에 맡길 수 있는 어린이집은 얼마나 있는가",
        "kind": "line",
        "csv": "childcare_time_flexible_facilities.csv",
        "source": "KOSIS DT_15407_NN009 특수보육어린이집 현황",
        "note": "야간 연장, 24시간, 휴일 보육 어린이집 수와 전체 어린이집 대비 비중을 계산했다. 특수보육 유형은 중복 지정될 수 있으므로 유형별 추세로 해석해야 한다.",
    },
    "openfiscal_debt_context": {
        "title": "열린재정 장기 재정 배경 지표",
        "kind": "line",
        "csv": "openfiscal_debt_context.csv",
        "source": "열린재정 Open API OPFI152",
        "note": "고령화와 생애주기 지출을 해석할 때 장기 재정 여건을 함께 보아야 한다.",
    },
    "openfiscal_aging_budget_trends": {
        "title": "고령화 관련 세부사업 수와 예산 금액 추세",
        "kind": "panel",
        "csv": "openfiscal_aging_budget_trends.csv",
        "source": "열린재정 VW_OPFI940 세부사업 예산편성현황(총지출), odtId=5Y5A50K2L4CW2IRKI2J0F2C8T",
        "note": "세부사업명에 노인, 고령, 기초연금, 기초노령연금, 장기요양, 치매, 경로당, 독거노인 등 고령화 관련 키워드가 포함된 사업을 추출했다. 금액은 당해연도 확정예산 성격의 Y_YY_DFN_MEDI_KCUR_AMT를 사용하고 조원 단위로 환산했다.",
    },
    "openfiscal_aging_budget_top_programs": {
        "title": "최근 연도 고령화 관련 상위 세부사업",
        "kind": "bar",
        "csv": "openfiscal_aging_budget_top_programs_latest.csv",
        "source": "열린재정 VW_OPFI940 세부사업 예산편성현황(총지출), odtId=5Y5A50K2L4CW2IRKI2J0F2C8T",
        "note": "최근 제공 연도의 고령화 관련 세부사업을 예산액 기준으로 정렬했다. 총액의 대부분이 기초연금과 장기요양, 노인일자리 사업에 집중되어 있는지 확인하는 보조 그림이다.",
    },
    "vacant_housing_rate": {
        "title": "전국 미거주주택(빈집) 비율",
        "kind": "line",
        "csv": "vacant_housing_rate.csv",
        "source": "KOSIS DT_1YL202005 미거주주택(빈집)비율, 국가데이터처·통계청 인구주택총조사 기준",
        "note": "조사시점의 미거주 주택 기준이다. 국토부 빈집실태조사의 1년 이상 장기 빈집 기준과 구분해 읽어야 한다.",
    },
    "household_population_gap_national": {
        "title": "전국 가구 수와 인구의 엇갈린 추세(2015=100)",
        "kind": "line",
        "csv": "household_population_gap_national.csv",
        "source": "KOSIS INH_1JC1501 가구수(시도/시/군/구), DT_1B040A3 행정구역(시군구)별 성별 주민등록인구수",
        "note": "가구 수는 인구총조사 가구, 인구는 주민등록인구를 시도 단위로 집계했다. 지수는 2015년을 100으로 둔 값이며, 평균 가구원 수는 주민등록인구/가구 수로 계산한 근사값이다.",
    },
    "household_population_gap_regions": {
        "title": "시도별 가구 수 증가율과 인구 증가율의 차이(2015-2024)",
        "kind": "bar",
        "csv": "household_population_gap_regions.csv",
        "source": "KOSIS INH_1JC1501 가구수(시도/시/군/구), DT_1B040A3 행정구역(시군구)별 성별 주민등록인구수",
        "note": "각 시도의 2015년 대비 2024년 변화율이다. 수도권뿐 아니라 대부분 지역에서 인구보다 가구 수가 더 빠르게 증가한다.",
    },
    "household_head_age_shift": {
        "title": "가구주의 고령화와 청년·고령 1인가구의 동시 증가",
        "kind": "line",
        "csv": "household_head_age_shift.csv",
        "source": "KOSIS DT_1JC1511 가구주의 연령 및 가구원수별 가구(일반가구) - 시군구, 전국",
        "note": "청년 1인가구는 가구주 20-34세 1인 가구로 정의했다. 고령 가구주는 65세 이상이며, 비중은 일반가구 전체 대비 비율이다.",
    },
    "household_one_person_age_index": {
        "title": "연령별 1인가구 증가 속도(2015=100)",
        "kind": "line",
        "csv": "household_head_age_shift.csv",
        "source": "KOSIS DT_1JC1511 가구주의 연령 및 가구원수별 가구(일반가구) - 시군구, 전국",
        "note": "총 일반가구, 전체 1인가구, 20-34세 1인가구, 65세 이상 1인가구를 2015년=100으로 환산해 비교했다.",
    },
    "national_population_pressure": {
        "title": "전국 인구구조 압력: 고령화율·노년부양비·중위연령",
        "kind": "line",
        "csv": "national_population_pressure.csv",
        "source": "KOSIS DT_1BPB002 주요 인구지표, 중위추계",
        "note": "저출산 정책은 출산율뿐 아니라 생산연령 인구, 고령화율, 부양비가 함께 움직이는 구조 속에서 평가해야 한다.",
    },
    "aging_index_growth": {
        "title": "노령화지수와 유소년·고령 인구 비중",
        "kind": "line",
        "csv": "aging_index_growth.csv",
        "source": "KOSIS DT_1BPB002 주요 인구지표, 중위추계",
        "note": "노령화지수는 유소년인구 100명당 65세 이상 인구 수다. 100을 넘으면 고령 인구가 유소년 인구보다 많다는 뜻이며, 한국은 2017년에 100을 넘어섰다.",
    },
    "sigungu_aging_distribution": {
        "title": "2024년 시군구 고령화율 분포",
        "kind": "bar",
        "csv": "sigungu_aging_distribution.csv",
        "source": "KOSIS DT_1B04006 행정구역(시군구)별/1세별 주민등록인구",
        "note": "일부 지역의 초고령 구조는 전국 평균보다 훨씬 앞서 나타난다.",
    },
    "childcare_capacity_pressure": {
        "title": "보육아동수·어린이집 수·시설당 아동수",
        "kind": "line",
        "csv": "childcare_capacity_pressure.csv",
        "source": "KOSIS DT_15407_NN001 어린이집 설치현황, DT_15407_NN002 어린이집 보육아동 현황",
        "note": "출생 감소는 돌봄 수요 감소와 시설 유지 압력을 동시에 만든다.",
    },
    "foreigner_registered_total": {
        "title": "등록외국인 규모 추세",
        "kind": "line",
        "csv": "foreigner_registered_total.csv",
        "source": "KOSIS DT_1B040A11 시군구별 및 체류자격별 등록외국인 현황",
        "note": "외국인 유입은 지역 노동시장과 가족 형성 구조를 함께 바꾸는 인구정책 변수다.",
    },
    "vacant_housing_policy": {
        "title": "빈집 수와 전체 주택",
        "kind": "line",
        "csv": "vacant_housing_policy.csv",
        "source": "KOSIS DT_1YL202005 미거주주택(빈집)비율, 국가데이터처·통계청 인구주택총조사 기준",
        "note": "미거주 주택의 넓은 저량과 전체 주택 재고를 함께 보여주는 그림이다. 비율 추세는 아래 보조 그림에서 따로 제시한다.",
    },
    "vacant_housing_definition_gap_2022": {
        "title": "빈집 통계 기준별 전국 비교(2022)",
        "kind": "bar",
        "csv": "vacant_housing_definition_gap_2022.csv",
        "source": "KOSIS DT_1YL202005 미거주주택(빈집)비율, 관계부처합동 보도자료 「전국 빈집 현황 정확하게 파악 가능해진다」(2023.6.8.)",
        "note": "KOSIS는 조사시점의 미거주 주택, 관계부처 빈집실태조사는 1년 이상 거주 또는 사용하지 않은 장기 빈집 기준이다.",
    },
    "molit_vacant_housing_2022": {
        "title": "국토교통부 등 빈집실태조사 기준 장기 빈집 구성(2022)",
        "kind": "bar",
        "csv": "molit_vacant_housing_2022.csv",
        "source": "관계부처합동 보도자료 「전국 빈집 현황 정확하게 파악 가능해진다」 붙임3 전국 빈집 현황(2022년도 기준)",
        "note": "도시지역은 소규모주택정비법, 농촌·어촌지역은 농어촌정비법 기준으로 조사된 값이며 일부 지역은 중복 조사 가능성이 있다.",
    },
    "fiscal_aging_pressure": {
        "title": "고령화와 재정 압력 지수",
        "kind": "line",
        "csv": "fiscal_aging_pressure.csv",
        "source": "KOSIS DT_1BPB002, 열린재정 OPFI152",
        "note": "국가채무와 고령화율을 기준연도 지수로 놓으면 재정 여건과 인구구조 압력이 함께 커지는 흐름을 볼 수 있다.",
    },
    "fertility_age_pattern": {
        "title": "모의 연령별 출산율 변화",
        "kind": "line",
        "csv": "fertility_age_pattern.csv",
        "source": "KOSIS DT_1B81A21 시도/합계출산율 모의 연령별 출산율",
        "note": "출산 감소는 특정 연령의 감소만이 아니라 출산 시점의 지연과 포기가 함께 만든 결과다.",
    },
    "fertility_measure_summary": {
        "title": "출산율 측정방식별 추세(2000=100)",
        "kind": "line",
        "csv": "fertility_measure_summary.csv",
        "source": "KOSIS DT_1B81A21, DT_1B8000H, DT_1BPA001",
        "note": "합계출산율, 조출생률, 일반출산율은 모두 출산을 보지만 분모와 해석 단위가 다르다.",
    },
    "fertility_asfr_shift": {
        "title": "연령별 출산율로 본 출산 시기의 이동",
        "kind": "line",
        "csv": "fertility_asfr_shift.csv",
        "source": "KOSIS DT_1B81A21 시도/합계출산율 모의 연령별 출산율",
        "note": "연령별 출산율은 출산이 어느 생애 단계에서 이루어지는지를 직접 보여준다.",
    },
    "cohort_fertility_by_birth_year": {
        "title": "여성 출생코호트별 누적 출산율(20-39세)",
        "kind": "line",
        "csv": "cohort_fertility_by_birth_year.csv",
        "source": "KOSIS DT_1B81A21 연령별 출산율을 여성 출생연도 기준으로 재배열",
        "note": "완결출산율은 가임기가 끝난 뒤에야 확정되므로, 여기서는 20-39세 관측 구간의 누적 출산율로 세대 차이를 비교한다.",
    },
    "mean_birth_age_order": {
        "title": "첫째·둘째아 평균 출산연령",
        "kind": "line",
        "csv": "mean_birth_age_order.csv",
        "source": "KOSIS DT_1B81A20 시도/출산순위별 모의 평균 출산연령",
        "note": "첫째아 출산연령 상승은 둘째아 이상 출산 가능성을 좁히는 중요한 경로다.",
    },
    "vital_events_policy": {
        "title": "출생·사망·혼인·이혼 건수",
        "kind": "line",
        "csv": "vital_events_policy.csv",
        "source": "KOSIS DT_1B8000H 시도/인구동태건수 및 동태율",
        "note": "출산정책은 출생만이 아니라 혼인 감소, 사망 증가, 자연증가 전환 속에서 읽어야 한다.",
    },
    "marriage_attitude_unmarried_gender": {
        "title": "미혼 남녀의 결혼 긍정 인식 변화",
        "kind": "bar",
        "csv": "marriage_attitude_unmarried_gender.csv",
        "source": "국가데이터처·통계청, 2010년 사회조사 결과 및 2024년 사회조사 결과",
        "note": "미혼 남녀 중 결혼을 해야 한다고 보는 비중이다. 2010년은 15세 이상, 2024년은 13세 이상 사회조사 기준이므로 장기 방향을 읽는 지표로 사용한다.",
    },
    "family_norms_culture_shift": {
        "title": "동거와 비혼 출산을 둘러싼 가족 규범의 변화",
        "kind": "line",
        "csv": "family_norms_culture_shift.csv",
        "source": "국가데이터처·통계청, 2010년 사회조사 결과 및 2024년 사회조사 결과",
        "note": "결혼 필요성은 약해졌고, 동거와 비혼 출산에 대한 수용은 높아졌다. 다만 한국의 제도와 출산 관행은 여전히 혼인 안 출산을 중심으로 작동한다.",
    },
    "divorce_rate_30s_40s_trend": {
        "title": "30대와 40대의 성별 연령별 이혼율",
        "kind": "line",
        "csv": "divorce_rate_30s_40s_trend.csv",
        "source": "KOSIS DT_1B85009 시도/성/연령별 이혼율, 전국 계, 2000-2024년",
        "note": "30대는 30-34세와 35-39세, 40대는 40-44세와 45-49세의 해당연령 천명당 이혼율을 단순 평균했다. 남편과 아내는 각각 해당 성·연령 인구 천명당 이혼건수다.",
    },
    "divorce_acceptance_trend": {
        "title": "이혼 수용 인식의 변화",
        "kind": "line",
        "csv": "divorce_acceptance_trend.csv",
        "source": "국가데이터처·통계청, 2024년 사회조사 결과 보도자료; KOSIS DT_1SSFA070R 이혼에 대한 견해",
        "note": "‘이유가 있으면 이혼을 하는 것이 좋다’ 응답 비중의 추세다. 2024년에는 20.5%로 2014년 12.0%보다 높아졌다.",
    },
    "divorce_acceptance_profile_2024": {
        "title": "2024년 집단별 이혼에 대한 견해",
        "kind": "bar",
        "csv": "divorce_acceptance_profile_2024.csv",
        "source": "국가데이터처·통계청, 2024년 사회조사 결과 보도자료; KOSIS DT_1SSFA070R 이혼에 대한 견해",
        "note": "부정은 ‘이혼해서는 안 된다’, 중립은 ‘할 수도 있고 하지 않을 수도 있다’, 긍정은 ‘이유가 있으면 하는 것이 좋다’ 응답이다.",
    },
    "marriage_attitude_youth_profile_2022": {
        "title": "청년의 결혼 긍정 인식: 연령대와 성별",
        "kind": "bar",
        "csv": "marriage_attitude_youth_profile_2022.csv",
        "source": "국가데이터처·통계청, 「사회조사」로 살펴본 청년의 의식변화(2023.8.28.)",
        "note": "청년은 19-34세 기준이다. 공개 보도자료는 연령대와 성별을 각각 공표하며, 연령×성별 교차값은 제공하지 않는다. 따라서 25-29세 여성의 직접 추정치가 아니라 청년 여성과 25-29세 연령대의 구조를 함께 읽는 보조 지표다.",
    },
    "young_women_25_29_recent_attitudes": {
        "title": "만 25-29세 여성의 결혼·자녀 인식 변화",
        "kind": "bar",
        "csv": "young_women_25_29_recent_attitudes.csv",
        "source": "저출산고령사회위원회, 결혼·출산·양육 및 정부 저출생 대책 인식조사(2024.3, 2025.3)",
        "note": "사회조사의 결혼 필요성 문항과 달리 결혼 의향·자녀 필요성 문항이다. 20대 후반 여성의 최근 인식이 반등하고 있지만, 자녀 필요성은 결혼 의향보다 낮은 수준에서 움직인다.",
    },
    "tfr_gender_conflict_timeline": {
        "title": "합계출산율 급락과 남녀 갈등 인식의 시간표",
        "kind": "line",
        "csv": "tfr_gender_conflict_timeline.csv",
        "source": "KOSIS DT_1B81A21 합계출산율; 한국행정연구원 사회통합실태조사(2013-2023) 재인용 KOSSDA 교육자료",
        "note": "남녀 갈등은 ‘매우 심각하다’ 응답 비율이다. 두 지표의 시간적 겹침은 문화적 환경을 해석하기 위한 단서이며, 인과효과로 단정해서는 안 된다.",
    },
    "living_population_ratio_top": {
        "title": "생활인구가 주민등록인구보다 큰 지역",
        "kind": "bar",
        "csv": "living_population_2025q3_summary.csv",
        "source": "행정안전부·통계청, 2025년 3분기 인구감소지역 생활인구 산정결과",
        "note": "생활인구는 월별 주민등록인구, 체류인구, 외국인을 합산한 값이다. 2025년 7-9월 평균을 사용했으며, 대상은 공표자료에 포함된 인구감소지역이다.",
    },
    "mobile_inflow_top_sigungu": {
        "title": "시군구별 통신 모바일 유입 이동량 상위 지역",
        "kind": "bar",
        "csv": "mobile_inflow_sigungu_2025_summary.csv",
        "source": "통계청 통계데이터센터, 통신 모바일 인구이동량 통계 시군구 관내외 유입 자료(~2026.04.26)",
        "note": "2025년 52개 주차의 주차별 일평균 이동건수 평균이다. 거주지와 목적지가 같은 귀가 이동은 집계하지 않으며, 관외는 거주 시군구 밖에서 해당 시군구로 들어온 이동이다.",
    },
    "mobile_outside_migration_by_sex": {
        "title": "남성과 여성의 관외 이동 추세",
        "kind": "line",
        "csv": "mobile_outside_migration_by_sex.csv",
        "source": "통계청 통계데이터센터, 통신 모바일 인구이동량 통계 성연령별 자료(~2026.04.26)",
        "note": "전국 성별 이동량 자료에서 관외 이동을 연도별 주차 평균으로 계산했다. 2026년은 4월 4주차까지의 부분 연도이므로 장기 추세선이 아니라 최신 관찰값으로 읽어야 한다.",
    },
    "living_population_ratio_map": {
        "title": "시군구별 주민등록인구 대비 생활인구 배율",
        "kind": "map",
        "csv": "living_population_2025q3_map_values.csv",
        "source": "행정안전부·통계청, 2025년 3분기 인구감소지역 생활인구 산정결과; 통계청 시군구 경계",
        "note": "2025년 7-9월 생활인구 월평균을 주민등록인구 월평균으로 나눈 값이다. 공표 대상인 인구감소지역만 색으로 표시하고, 그 외 시군구는 회색으로 남겼다.",
    },
    "living_population_age_component": {
        "title": "생활인구 구성별 연령 분포",
        "kind": "bar",
        "csv": "living_population_2025q3_age_component.csv",
        "source": "행정안전부·통계청, 2025년 3분기 인구감소지역 생활인구 산정결과",
        "note": "인구감소지역 공표자료의 2025년 7-9월 월별 값을 합산한 뒤 월평균으로 환산했다. 주민등록인구, 체류인구, 외국인, 생활인구 전체의 연령 구성을 비교한다.",
    },
    "living_population_sex_component": {
        "title": "생활인구 구성별 성별 분포",
        "kind": "bar",
        "csv": "living_population_2025q3_sex_component.csv",
        "source": "행정안전부·통계청, 2025년 3분기 인구감소지역 생활인구 산정결과",
        "note": "인구감소지역 공표자료의 2025년 7-9월 월별 값을 합산한 뒤 월평균으로 환산했다. 성별 차이는 정주인구와 체류인구가 서로 다른 생활 기능을 갖는지 확인하기 위한 보조 지표다.",
    },
    "living_population_monthly_trend": {
        "title": "생활인구 구성별 월별 변화",
        "kind": "line",
        "csv": "living_population_2025q3_monthly_trend.csv",
        "source": "행정안전부·통계청, 2025년 3분기 인구감소지역 생활인구 산정결과",
        "note": "2025년 7-9월 3개월 자료이므로 장기 추세가 아니라 여름 성수기에서 초가을로 넘어가는 짧은 계절 변화로 해석해야 한다.",
    },
    "sido_net_migration_panel": {
        "title": "광역시도별 순이동 추세(2000-2025)",
        "kind": "panel",
        "csv": "sido_net_migration_total.csv",
        "source": "KOSIS DT_1B26001_A03 시군구/연령(5세)별 이동자수, 광역시도 순이동",
        "note": "순이동은 총전입에서 총전출을 뺀 값이다. 각 패널의 세로축은 해당 지역의 변동 범위에 맞추어 조정했으므로, 지역 간 절대 규모 비교는 제목의 최근 10년 평균과 최신연도 값을 함께 보아야 한다.",
    },
    "sido_net_migration_age_contribution": {
        "title": "광역시도 순이동의 연령대별 기여(2016-2025년 평균)",
        "kind": "bar",
        "csv": "sido_net_migration_age_contribution.csv",
        "source": "KOSIS DT_1B26001_A03 시군구/연령(5세)별 이동자수, 광역시도 순이동",
        "note": "연령대별 순이동을 0-14세, 15-19세, 20-24세, 25-29세, 30-34세, 35-44세, 45-64세, 65세 이상으로 묶어 최근 10년 평균을 계산했다. 막대의 합은 해당 지역의 평균 순이동이다.",
    },
    "young_migration_policy": {
        "title": "서울·경기 20대·30대 순이동",
        "kind": "line",
        "csv": "young_migration_policy.csv",
        "source": "KOSIS DT_1B26001_A03 시군구/연령(5세)별 이동자수",
        "note": "청년의 수도권 내부 이동은 출산·주거·지역 노동시장 조건을 함께 보여준다.",
    },
    "future_households_policy": {
        "title": "장래가구: 1인가구와 총가구",
        "kind": "line",
        "csv": "future_households_policy.csv",
        "source": "KOSIS DT_1BZ0503 가구주의 연령/가구원수별 추계가구-전국",
        "note": "인구가 줄어도 1인가구와 고령가구 증가 때문에 가구수와 주거 수요는 다른 궤적을 보인다.",
    },
}


SECTION_SUPPLEMENTAL_CHARTS = {
    "section-1-1-age-structure.html": ["national_population_pressure"],
    "section-1-2-population-measures.html": ["population_measure_gap"],
    "section-1-3-2010-registration-jump.html": ["resident_registration_centenarian_trend"],
    "section-1-4-fertility-measures.html": ["fertility_asfr_shift", "cohort_fertility_by_birth_year", "mean_birth_age_order"],
    "section-2-5-international-low-fertility.html": ["international_tfr_europe", "fertility_family_structure_comparison"],
    "section-2-1-housing-support-marriage-birth.html": [
        "housing_tenure_young_newlywed",
        "housing_finance_burden_by_age",
        "youth_housing_consumption_pressure",
        "international_housing_fertility_cases",
        "housing_security_outcomes_national",
        "capital_region_housing_marriage_birth",
        "housing_security_outcome_regression",
    ],
    "section-2-1-yeonggwang-cohort.html": ["birth_incentive_region_summary", "national_population_pressure"],
    "section-2-2-fertility-conditions.html": ["fertility_age_pattern", "vital_events_policy", "mean_birth_age_order", "newlywed_income_fertility", "youth_employment_context"],
    "section-3-0-living-population.html": ["mobile_inflow_top_sigungu"],
    "section-3-1-regional-gap.html": ["young_migration_policy", "sigungu_aging_distribution"],
    "section-3-2-foreign-multicultural.html": ["foreigner_registered_total"],
    "section-4-1-family-formation.html": ["fertility_age_pattern", "mean_birth_age_order"],
    "section-4-1-divorce-fear-marriage.html": ["divorce_acceptance_trend", "divorce_acceptance_profile_2024"],
    "section-4-2-men-care-parental-leave.html": [
        "maternity_leave_support",
        "parental_leave_per_user_support",
        "preschool_childcare_time_by_parent",
        "dual_earner_child_housework_time",
    ],
    "section-4-3-care-work-balance.html": ["childcare_capacity_pressure"],
    "section-4-4-childcare-shortage.html": ["childcare_users_by_type", "childcare_capacity_pressure"],
    "section-4-5-households.html": ["household_population_gap_regions"],
    "section-4-6-housing-demand.html": ["household_population_gap_national"],
    "section-4-7-vacant-housing.html": ["vacant_housing_rate"],
    "section-5-1-labor-aging.html": [],
    "section-5-3-lifecycle-fiscal.html": ["fiscal_aging_pressure"],
    "section-5-4-aging-budget.html": ["openfiscal_aging_budget_top_programs", "fiscal_aging_pressure"],
    "section-5-5-elderly-pension.html": ["national_population_pressure"],
    "section-6-2-private-education-by-school-level.html": ["high_school_private_education_drivers"],
    "section-6-3-education-cost-inequality.html": ["newlywed_income_fertility"],
}


SECTION_FRONT_CONTEXT = {
    "section-5-1-labor-aging.html": {
        "heading": "구조적 배경: 고령화율·노년부양비·중위연령이 먼저 움직인다",
        "chart": "national_population_pressure",
        "paragraphs": [
            "고령층 노동시장을 보기 전에 먼저 확인해야 할 것은 인구구조의 압력이다. 고령화율은 사회 안에서 65세 이상 인구가 차지하는 비중을 보여주고, 노년부양비는 생산연령 인구 100명이 감당해야 하는 고령 인구의 크기를 보여준다. 중위연령은 전체 인구를 나이순으로 세웠을 때 한가운데 있는 사람의 나이다. 이 세 지표가 동시에 올라간다는 것은 한국 사회의 중심 연령이 위로 이동하고, 일하는 세대와 돌봄을 필요로 하는 세대의 비율이 다시 짜이고 있다는 뜻이다.",
            "이 그림은 고령층 고용을 단순히 ‘노인이 더 일한다’는 현상으로 보지 않게 만든다. 생산연령 인구가 얇아지고, 고령 인구의 비중이 커지며, 사회 전체의 중위연령이 높아지면 노동시장은 자연스럽게 더 나이 든 사람의 노동에 의존하게 된다. 기업은 채용 가능한 청년층이 줄어드는 상황을 맞고, 국가는 연금·의료·돌봄 지출이 커지는 상황을 맞는다. 이 두 압력이 만나는 지점에서 고령층 경제활동이 정책의 중심 문제로 떠오른다.",
            "따라서 6.1절의 질문은 고령층 노동을 예외적 현상으로 보는 데서 출발하지 않는다. 오히려 인구구조가 이미 노동시장에 던진 질문에 답하는 과정이다. 고령층에서 취업자와 고용률이 얼마나 빨리 늘어나는지, 실업자와 비경제활동인구가 어떤 속도로 변하는지를 보는 이유도 여기에 있다. 고령화율과 노년부양비의 상승은 배경지표가 아니라, 뒤따르는 노동시장 변화의 원인을 설명하는 첫 장면이다.",
        ],
    },
}


SECTION_INDEPENDENT_ANALYSIS = {
    "section-5-1-labor-aging.html": {
        "heading": "지역 회귀분석: 고령층 노동시장의 속도는 지역마다 다르다",
        "chart": "elderly_regional_labor_60plus_slopes",
        "paragraphs": [
            "전국 추세는 한국 사회가 어느 방향으로 움직이는지 보여주지만, 지역 정책을 설계하려면 변화의 속도가 어디에서 빠른지 따로 보아야 한다. 이를 위해 시도별 60세 이상 자료에 대해 연도만을 독립변수로 두고 단순 회귀분석을 했다. 여기서 회귀계수는 인과효과가 아니라 ‘2010-2025년 동안 매년 평균적으로 얼마나 변했는가’를 요약한 값이다.",
            "취업자 증가 속도는 경기도가 연평균 77.1천 명으로 가장 크고, 서울특별시가 34.7천 명으로 뒤를 잇는다. 이는 수도권에서 고령 인구 자체가 크게 늘고, 은퇴 이후에도 일하는 사람이 빠르게 증가했음을 뜻한다. 경상남도와 부산광역시, 인천광역시도 뒤따르는데, 이 차이는 지역의 고령화 속도뿐 아니라 산업구조와 일자리 규모의 차이까지 함께 반영한다.",
            "고용률의 회귀계수는 조금 다른 이야기를 한다. 취업자 수의 증가가 큰 지역이 반드시 고용률 상승도 가장 큰 것은 아니다. 강원도는 연평균 1.31%포인트, 세종특별자치시는 1.19%포인트, 충청북도는 1.14%포인트 상승해 고령층이 실제 노동시장에 편입되는 속도가 빠른 편이다. 반대로 큰 도시는 고령 인구와 취업자가 함께 늘어도 노동시장 밖에 있는 고령층도 동시에 늘 수 있다.",
            "실업자는 모든 지역에서 취업자나 비경제활동인구보다 훨씬 작은 폭으로 움직인다. 그래서 고령층 노동 문제를 실업률만으로 읽으면 핵심을 놓치기 쉽다. 더 큰 변화는 비경제활동인구에서 나타난다. 일하고 있는 고령층과 노동시장 밖에 있는 고령층이 동시에 커지는 구조는, 고령층 정책이 고용정책 하나로 끝날 수 없다는 사실을 보여준다.",
            "이 그림의 결론은 단순하지 않다. 어떤 지역은 고령층 일자리를 더 많이 만들어야 하고, 어떤 지역은 일할 수 없는 고령층의 소득과 돌봄을 더 촘촘하게 보아야 한다. 고령사회 노동정책은 전국 평균 고용률 하나로 설계될 수 없다. 지역별 회귀계수의 분포는 각 지역이 ‘더 오래 일하는 사회’와 ‘일을 멈출 수 없는 사회’ 사이에서 어디쯤 서 있는지 묻는 출발점이다.",
        ],
    },
}


SECTION_ANALYSIS = {
    "section-1-1-age-structure.html": {
        "heading": "분석: 피라미드는 한국 현대사의 지층을 보여준다",
        "paragraphs": [
            "1980년 피라미드에서는 10대 후반과 20대 초반이 두껍다. 이들은 대체로 1950년대 후반부터 1960년대 초반에 태어난 전후 베이비붐 세대다. 반대로 20대 후반 일부가 상대적으로 얇게 보이는 것은 한국전쟁기와 전후 혼란기에 출생이 줄었던 흔적이다.",
            "1990년에는 베이비붐 세대가 20대 후반과 30대 초반으로 이동해 노동시장과 혼인시장 중심부를 형성한다. 동시에 0-9세의 밑부분은 1970년대 이후 가족계획사업, 도시화, 여성 교육 확대, 양육비 상승이 누적되며 1980년대 출생아 수가 줄어든 결과로 좁아진다.",
            "2020년과 2025년 피라미드는 더 이상 피라미드가 아니라 항아리에 가깝다. 1955-1963년생 전후 베이비붐 세대는 2020년에 50대 후반-60대 중반, 2025년에 60대 초중반-70세 전후로 이동해 위쪽을 두껍게 만든다. 반면 1997년 외환위기 이후 청년층의 고용·주거 불안, 2000년대 이후 만혼과 초저출산, 2015년 이후 출생아 급감은 20대 이하와 유소년층의 급격한 축소로 나타난다.",
            "남녀를 나누어 보면 고령층에서 여성 쪽이 더 두껍다. 이는 여성 기대수명이 더 길기 때문이다. 따라서 고령화는 단순히 노인이 많아지는 현상이 아니라, 독거·돌봄·의료·빈곤 위험이 성별로 다르게 나타나는 구조 변화다."
        ],
    },
    "section-1-2-population-measures.html": {
        "heading": "분석: 인구 기준을 바꾸면 결론도 바뀐다",
        "paragraphs": [
            "성비와 인구성장률은 인구를 읽기 전에 확인해야 할 배경 지표다. 같은 총인구라도 주민등록인구, 연앙인구, 인구총조사는 측정 목적이 다르기 때문에 출산율의 분모, 지역 인구의 기준, 정책 대상 규모가 달라질 수 있다.",
            "인구성장률이 0에 가까워지거나 음수로 전환되는 시점은 ‘인구감소 사회’의 시작점처럼 보이지만, 실제 정책 현장에서는 어느 자료원을 쓰느냐가 중요하다. 주민등록인구는 행정 서비스 수요를, 인구총조사는 거주 실태를, 인구동태 연앙인구는 출생·사망률 계산의 기준을 더 잘 설명한다.",
            "따라서 이 절은 이후 모든 장의 기준표 역할을 한다. 지표를 비교한 뒤, 장별 분석에서 어떤 기준을 왜 선택했는지 계속 밝혀야 한다."
        ],
    },
    "section-2-1-yeonggwang-cohort.html": {
        "heading": "분석: 높은 출산지원은 지역 잔존을 보장하지 않는다",
        "paragraphs": [
            "이 절은 영광군 한 곳의 사례를 5개 군 비교로 넓힌다. 영광군, 강진군, 고흥군, 해남군, 진도군은 출산장려금이나 양육수당을 적극적으로 운영해 온 지역으로 분류할 수 있지만, 같은 현금지원형 정책이라도 0세 인구가 4년 뒤 지역에 남는 정도는 크게 달랐다.",
            "2013-2020년 출생 코호트를 2017-2024년 4세 인구와 연결해 보면 평균 잔존율은 고흥군 96.08%, 진도군 93.17%, 영광군 81.20%, 강진군 70.11%, 해남군 57.82% 순이었다. 고흥군과 진도군은 일부 연도에서 4세 인구가 0세보다 많아 전입 효과가 출생 코호트를 보강한 반면, 해남군과 강진군은 태어난 아이의 상당수가 4세가 되기 전에 다른 지역으로 이동한 것으로 읽힌다.",
            "이 결과를 출산장려금의 실패나 성공으로 곧장 판정해서는 안 된다. 0세→4세 잔존율에는 출생지원금, 부모의 일자리, 주거, 어린이집 접근성, 초등학교 진학 전 이주, 주민등록 이전이 함께 섞여 있다. 다만 분명한 것은 있다. 출산정책의 성과를 출생아 수나 합계출산율에서 멈추면, 지역이 실제로 아이와 가족을 붙잡았는지 보지 못한다."
        ],
    },
    "section-2-2-fertility-conditions.html": {
        "heading": "분석: 출산 지연은 혼인·고용·소득이 만나는 지점에서 만들어진다",
        "paragraphs": [
            "전국 합계출산율은 2000년 1.480에서 2024년 0.750으로 낮아졌지만, 이 숫자는 원인이 아니라 결과에 가깝다. 같은 기간 혼인은 줄고, 첫째아 출산연령은 높아졌으며, 청년층의 노동시장 진입과 주거 형성은 더 늦고 불안정해졌다.",
            "한국처럼 출산이 혼인과 강하게 연결된 사회에서는 혼인의 지연이 곧 출산의 지연으로 이어진다. 첫째아 출산이 늦어지면 둘째아 이상으로 이어질 시간도 줄어든다. 따라서 출산율 하락은 ‘아이를 원하지 않는다’보다 ‘아이를 낳을 수 있는 생활 조건이 늦게 도착한다’는 문장으로 읽는 편이 더 정확하다.",
            "소득 자료도 단순하지 않다. 신혼부부 통계에서 소득은 대체로 근로·사업소득, 즉 고용의 결과다. 소득이 낮으면 양육비와 주거비를 감당하기 어렵고, 소득이 높아도 안정적 일자리와 장시간 노동, 경력 경쟁이 결혼과 출산의 시점을 늦출 수 있다. 소득은 출산을 자동으로 늘리는 스위치가 아니라, 고용 안정과 생애 시간표 속에서 해석해야 하는 조건이다."
        ],
    },
    "section-3-1-regional-gap.html": {
        "heading": "분석: 전국 평균은 지역의 속도 차이를 가린다",
        "paragraphs": [
            "2024년 시군구 고령화율 상위 지역을 보면 의성군 47.48%, 군위군 47.32%, 고흥군 45.69%처럼 일부 군 지역은 이미 주민 두 명 중 한 명 가까이가 65세 이상이다. 전국 평균만 보면 이 속도 차이가 사라진다.",
            "지역 격차 장에서는 고령화율을 출발점으로 삼되, 청년 순이동과 연령별 전출입 자료를 붙여야 한다. 고령화율이 높은 지역은 단지 노인이 많아서가 아니라 청년과 가족 형성 연령층이 빠져나간 결과일 수 있다.",
            "따라서 GIS는 장식이 아니라 분석 도구다. 같은 지표를 시군구 지도에 올리면 어느 지역이 먼저 학교, 보육, 의료, 돌봄, 노동력 부족 문제를 겪을지 가늠할 수 있다."
        ],
    },
    "section-3-2-foreign-multicultural.html": {
        "heading": "분석: 지역 인구는 내국인 출생만으로 설명되지 않는다",
        "paragraphs": [
            "전국 다문화 출생 비중은 2008년 2.9%에서 2024년 5.6%로 높아졌다. 출생아 수가 줄어드는 상황에서 다문화 출생의 비중이 커지는 것은 가족 형성 구조가 바뀌고 있다는 뜻이다.",
            "이 절은 외국인주민, 체류자격, 국제결혼, 다문화 출생을 하나의 흐름으로 읽는다. 노동 목적으로 들어온 외국인, 유학생, 결혼이민자, 장기체류자는 지역사회에 서로 다른 방식으로 남는다.",
            "추가 분석에서는 법무부 체류외국인과 행안부 외국인주민 자료를 지역별로 붙여, 어떤 지역에서 외국인 유입이 노동시장 보완인지 가족 형성의 통로인지 구분한다."
        ],
    },
    "section-4-1-family-formation.html": {
        "heading": "분석: 혼인과 출생은 한국에서 강하게 묶여 있다",
        "paragraphs": [
            "한국의 출산은 여전히 혼인과 강하게 연결되어 있다. 따라서 출산율만 낮아졌다고 말하기보다 혼인율, 이혼율, 출생률이 지역과 시점에 따라 어떻게 함께 움직이는지 봐야 한다.",
            "현재 이 절의 기본 차트는 출산율 비교를 사용해 가족 형성 조건의 배경을 보여준다. 다음 분석 단계에서는 KOSIS 인구동태의 조혼인율, 조이혼율, 조출생률을 시도 패널로 구성해 산점도와 회귀분석을 추가한다.",
            "해석의 핵심은 혼인을 늘리면 출생이 자동으로 늘어난다는 단순 결론을 피하는 것이다. 혼인과 출생의 상관은 주거, 소득, 일자리, 성평등한 돌봄 조건에 의해 매개된다."
        ],
    },
    "section-4-3-care-work-balance.html": {
        "heading": "분석: 보육 수요 감소는 돌봄 인프라 위기의 신호다",
        "paragraphs": [
            "어린이집 보육아동수는 2017년 145만 명 수준에서 2024년 94만 명 수준으로 줄었다. 이는 출생아 수 감소가 돌봄 인프라의 유지 가능성으로 이어지는 과정을 보여준다.",
            "보육아동수가 줄면 단기적으로는 시설 수요가 줄어드는 것처럼 보이지만, 지역에서는 어린이집 폐원과 접근성 악화가 다시 정주 여건을 나쁘게 만들 수 있다. 돌봄 인프라가 사라진 지역은 젊은 가족이 남기 더 어려워진다.",
            "후속 분석에서는 육아휴직 이용자 수, 남성 육아휴직 비중, 산업별 육아휴직 이용 차이를 결합해 ‘돌봄을 누가 감당하는가’라는 질문으로 확장한다."
        ],
    },
    "section-4-4-childcare-shortage.html": {
        "heading": "분석: 어린이집 부족은 총량보다 접근성의 문제다",
        "paragraphs": [
            "어린이집이 적어서 출산을 덜 하는가라는 질문은 겉보기보다 까다롭다. 전국 총량만 보면 2024년 어린이집은 2만7387개소, 보육아동은 94만1303명이고 시설당 아동수는 34.4명이다. 2000년의 시설당 35.6명, 2014년의 34.2명과 큰 차이가 없다. 그래서 단순히 ‘시설당 아이가 너무 많다’고 말하기는 어렵다.",
            "그러나 유형별로 보면 전혀 다른 그림이 나온다. 전체 어린이집 수는 2013년 4만3770개소로 정점을 찍은 뒤 2024년 2만7387개소로 줄었다. 특히 가정 어린이집은 2013년 2만3632개소에서 2024년 9586개소로, 민간 어린이집은 2014년 1만4822개소 정점 이후 2024년 8181개소로 줄었다. 반대로 국공립 어린이집은 2000년 1295개소에서 2024년 6521개소로 늘었고, 직장 어린이집도 204개소에서 1305개소로 커졌다.",
            "보육아동수도 같은 구조 전환을 보인다. 전체 보육아동은 2014년 149만6671명으로 정점을 찍은 뒤 2024년 94만1303명으로 줄었다. 민간 어린이집 이용 아동은 2014년 77만5414명에서 2024년 37만3524명으로 거의 절반 수준이 되었고, 가정 어린이집 이용 아동은 2012년 37만1671명 정점에서 2024년 13만9172명으로 크게 줄었다. 그 사이 국공립 이용 아동은 2024년 29만3049명까지 늘어났다.",
            "정책적으로 중요한 대목은 여기다. 출생아 수가 줄면 시장 기반 시설부터 먼저 흔들린다. 민간·가정 어린이집이 줄어드는 것은 단순한 조정처럼 보일 수 있지만, 어느 동네에서는 가장 가까운 보육 선택지가 사라지는 일이다. 국공립 확충은 질과 공공성을 높이는 방향이지만, 모든 생활권의 접근성 공백을 즉시 메우지는 못한다. 따라서 ‘어린이집이 적어서 출산을 덜 한다’는 명제는 전국 시설 수의 부족이 아니라, 아이를 낳은 뒤 실제로 맡길 수 있는 가까운 시설이 있는가의 문제로 다시 써야 한다.",
            "출산정책이 현금지원에 머물면 이 문제를 놓치기 쉽다. 부모가 계산하는 것은 첫해 지원금만이 아니라, 영아기부터 유아기까지 믿고 맡길 수 있는 시간표와 거리, 비용, 교사의 안정성이다. 보육 인프라가 빠르게 줄어드는 지역에서는 출산 감소가 시설 폐원을 낳고, 시설 폐원이 다시 출산과 정주 의향을 낮추는 순환이 생긴다."
        ],
    },
    "section-4-5-household-housing.html": {
        "heading": "분석: 인구 감소와 가구·주거 변화는 같은 속도로 움직이지 않는다",
        "paragraphs": [
            "전국 미거주주택 비율은 2015년 6.5%에서 2024년 8.0%로 높아졌다. 인구가 줄어도 1인가구와 고령가구가 늘면 가구수와 주택 수요는 한동안 다른 방향으로 움직일 수 있다.",
            "빈집은 단순히 집이 남는 문제가 아니라 지역의 생활권이 약해지는 신호다. 학교와 보육시설이 줄고, 상권과 의료 접근성이 약해지면 남은 가구의 정주 가능성도 함께 낮아진다.",
            "이 절의 다음 단계는 장래가구추계로 시도별 가구 정점연도를 계산하고, 빈집률 지도와 결합하는 것이다."
        ],
    },
    "section-5-1-labor-aging.html": {
        "heading": "분석: 청년 기반 축소는 노동시장 부족으로 이어진다",
        "paragraphs": [
            "e-나라지표 청년 고용동향의 생산가능인구 자료는 청년층 기반이 장기적으로 줄어드는 흐름을 보여준다. 청년 인구 감소는 혼인과 출산의 기반을 줄일 뿐 아니라 지역 노동시장 공급도 약하게 만든다.",
            "노동시장 장은 인구구조 변화가 실제 사업체의 인력부족률과 고령층 경제활동 증가로 어떻게 나타나는지 추적해야 한다. 고령층 취업 증가는 활력의 신호일 수도 있지만, 노후소득 불안의 결과일 수도 있다.",
            "추가 분석에서는 직종별사업체노동력조사의 규모별·지역별 인력부족률과 고령층 경제활동인구 자료를 결합해, 어떤 지역과 산업에서 인구구조 충격이 먼저 나타나는지 보인다."
        ],
    },
    "section-5-2-aging-index.html": {
        "heading": "분석: 노령화지수는 사회의 중심축이 어디로 이동했는지를 보여준다",
        "paragraphs": [
            "노령화지수는 0~14세 유소년 인구 100명당 65세 이상 인구가 몇 명인지를 보여주는 지표다. 고령화율이 전체 인구 중 노인의 비중을 묻는다면, 노령화지수는 사회의 아래쪽 세대와 위쪽 세대의 상대적 크기를 직접 비교한다. 그래서 이 지수는 학교와 돌봄, 노동시장과 연금, 지역 공동체의 세대 균형이 어느 방향으로 기울고 있는지를 읽는 데 특히 유용하다.",
            "한국의 노령화지수는 2000년 34.3이었다. 유소년 100명에 대해 65세 이상 인구가 34명 정도였다는 뜻이다. 그런데 2017년에 105.1로 100을 넘어서며 고령 인구가 유소년 인구보다 많아졌고, 2025년에는 199.9에 이른다. 이제 유소년 100명당 고령 인구가 거의 200명인 사회가 된 것이다.",
            "증가 속도는 더 중요하다. 2000년에서 2025년까지 노령화지수는 34.3에서 199.9로 올라 25년 동안 165.6포인트 증가했다. 연평균으로는 6.6포인트씩 오른 셈이다. 그러나 앞으로의 속도는 더 빠르다. 중위추계 기준으로 2052년에는 522.4까지 올라가며, 2025년 이후에는 연평균 11.9포인트씩 증가한다.",
            "이 지수가 빠르게 오르는 이유는 두 방향의 힘이 동시에 작용하기 때문이다. 하나는 65세 이상 인구 비중이 2000년 7.2%에서 2025년 20.3%, 2052년 40.8%로 커지는 힘이다. 다른 하나는 유소년 비중이 같은 기간 21.1%에서 10.2%, 7.8%로 줄어드는 힘이다. 노령화지수는 고령층이 많아지는 효과와 아이가 적어지는 효과를 한 숫자 안에 동시에 담는다.",
            "따라서 노령화지수는 단순히 ‘노인이 많아졌다’는 지표가 아니다. 유소년 인구가 줄어드는 속도와 고령 인구가 늘어나는 속도가 만나면서 사회의 세대 피라미드가 뒤집히는 정도를 보여준다. 이 절을 5.1절 뒤에 두는 이유도 여기에 있다. 고령층 노동, 연금, 장기요양, 고령화 예산은 모두 이 구조 변화가 노동시장과 재정으로 번역된 결과다."
        ],
    },
    "section-5-3-lifecycle-fiscal.html": {
        "heading": "분석: 인구 문제의 끝은 재정과 생애주기 부담이다",
        "paragraphs": [
            "열린재정 장기 재정 배경 지표에서 국가채무는 2013년 489.8에서 2029년 1788.9로 커지는 흐름을 보인다. 이 수치 자체가 저출산·고령화 비용을 직접 뜻하지는 않지만, 재정 여건을 함께 보아야 한다는 배경을 제공한다.",
            "고령화가 진행되면 보건·돌봄·연금 지출은 늘고, 생산연령 인구 감소는 세입 기반을 약하게 만들 수 있다. 그래서 생애주기 적자, 연령별 노동소득, 공공·민간 보건소비를 같은 표 안에 넣어야 한다.",
            "후속 분석에서는 국민이전계정 자료를 확보해 연령별 소비와 노동소득의 차이를 계산하고, 청년·대학·보육·노인돌봄 관련 열린재정 사업을 별도 묶음으로 추적한다."
        ],
    },
    "section-5-3-health-spending-aging.html": {
        "heading": "분석: 고령화의 압력은 의료비 곡선에서 가장 구체적으로 보인다",
        "paragraphs": [
            "연금은 고령화 재정을 설명할 때 가장 먼저 떠오르는 제도지만, 일상에서 더 직접적으로 체감되는 압력은 의료비다. 같은 노년이라도 65세, 75세, 85세 이후의 건강상태와 의료 이용은 크게 다르다.",
            "국민이전계정의 공공보건소비는 연령별로 공공부문을 통해 소비되는 보건 지출의 1인 규모를 보여준다. 총액 자료가 아니라 1인당 연령 프로필이기 때문에, 고령층 인구가 늘어나는 효과와 별도로 같은 나이의 사람이 공공보건 지출을 얼마나 더 필요로 하게 되었는지 읽게 해 준다.",
            "이 절은 의료비를 단순한 지출 억제 대상으로 보지 않는다. 건강수명, 만성질환 관리, 지역 의료 접근성, 장기요양과 의료의 연결을 함께 보아야 고령사회 의료비 증가의 의미를 정확히 해석할 수 있다."
        ],
    },
    "section-5-4-aging-budget.html": {
        "heading": "분석: 고령화 예산은 항목보다 금액이 먼저 커졌다",
        "paragraphs": [
            "열린재정 세부사업 예산편성현황에서 세부사업명에 노인, 고령, 기초연금, 기초노령연금, 장기요양, 치매, 경로당, 독거노인 등이 들어간 사업을 추려 보면, 고령화 예산은 2007년 0.4조 원 수준에서 2026년 29.2조 원 수준으로 커진다. 같은 기간 고유 세부사업명 수는 62개에서 36개로 줄어들었다. 겉으로 보이는 정책 항목은 오히려 정리되었지만, 몇 개의 큰 제도성 지출이 예산 전체를 끌어올린 셈이다.",
            "이 변화의 중심에는 기초노령연금에서 기초연금으로 이어지는 현금급여가 있다. 2008년 기초노령연금 예산이 본격적으로 잡히면서 고령화 예산은 2조 원대로 뛰고, 2014년 기초연금 도입 이후에는 증가 속도가 다시 가팔라진다. 2026년에는 기초연금지급만 23.1조 원으로, 이 절에서 추출한 고령화 관련 예산의 대부분을 차지한다.",
            "장기요양과 치매, 노인일자리 예산도 함께 커졌지만 규모의 성격은 다르다. 장기요양과 치매는 돌봄 필요가 제도적 서비스 수요로 전환되는 흐름을 보여주고, 노인일자리는 은퇴 이후 소득 보완과 사회참여를 동시에 겨냥한다. 그러나 이 둘을 합쳐도 기초연금의 재정 규모에는 미치지 못한다. 고령화 재정의 핵심 압력은 사업 수의 증가라기보다 권리성·준권리성 급여의 구조적 확대에 있다.",
            "전문가의 관점에서 중요한 것은 이 예산을 단순히 ‘노인에게 쓰는 돈이 늘었다’고 읽지 않는 것이다. 고령층 규모가 커지고 평균수명이 길어지는 사회에서 기초연금, 장기요양, 노인일자리 지출은 복지 확대의 결과이면서 동시에 재정 경직성의 원인이 된다. 매년 의무적으로 늘어나는 지출이 커질수록 정부가 경기 대응, 청년·아동 투자, 지역서비스 혁신에 쓸 수 있는 재량은 좁아진다. 고령화 예산 분석은 결국 한국 재정이 어떤 세대 간 계약을 선택할 것인가를 묻는 작업이다."
        ],
    },
    "section-5-5-elderly-pension.html": {
        "heading": "분석: 연금수령액은 늘었지만 성별 격차는 오래 남아 있다",
        "paragraphs": [
            "KOSIS 고령층 부가조사의 성별 연금수령여부 및 월평균수령액을 보면, 55~79세 연금수령자의 평균 월수령액은 2008년 40.8만원에서 2025년 86.1만원으로 늘었다. 명목 금액 기준으로 45.3만원, 111.0% 증가한 것이다. 같은 기간 연금수령률도 30.0%에서 51.7%로 높아졌다. 더 많은 고령층이 연금을 받게 되었고, 받는 사람의 평균 금액도 커진 셈이다.",
            "그러나 이 증가를 곧바로 노후소득 안정으로 읽기는 어렵다. 2025년 평균 수령액 86.1만원은 고령층의 생활비 전체를 감당하기에는 여전히 제한적이다. 더구나 이 값은 ‘연금을 받는 사람’의 평균이므로, 연금을 받지 못하는 55~79세까지 함께 고려하면 실제 노후소득 기반은 더 얇아진다.",
            "성별 격차는 이 표의 핵심이다. 남성의 평균 연금수령액은 2008년 54.4만원에서 2025년 112.0만원으로 늘었고, 여성은 22.4만원에서 58.8만원으로 늘었다. 여성의 증가율은 162.5%로 더 크지만, 2025년에도 여성 평균은 남성의 절반을 조금 넘는 수준이다. 과거 노동시장 참여, 임금, 경력단절, 국민연금 가입 이력의 차이가 노년기의 연금 격차로 이어진다.",
            "따라서 5.5절은 평균수령액과 수령률의 두 선을 먼저 읽는다. 연금제도가 더 넓게 작동하고 금액도 커졌다는 사실은 분명하다. 그러나 평균은 한 사회의 노후소득을 설명하는 출발점일 뿐이다. 실제로 어느 금액대에 사람이 몰려 있는지는 다음 절에서 따로 보아야 한다."
        ],
    },
    "section-5-6-elderly-pension-distribution.html": {
        "heading": "분석: 평균은 올라갔지만, 연금의 분포는 여전히 두껍고 낮다",
        "paragraphs": [
            "연금수령액의 평균이 높아졌다는 말은 중요하지만, 충분하지 않다. 평균은 낮은 금액을 받는 사람과 높은 금액을 받는 사람을 한 숫자로 섞어 버린다. 그래서 고령층 노후소득을 판단하려면 ‘평균이 얼마인가’와 함께 ‘어느 금액대에 얼마나 많은 사람이 몰려 있는가’를 따로 보아야 한다.",
            "2008년에는 55~79세 연금수령자 가운데 월평균 10만원 미만이 32.0%, 10~25만원 미만이 36.9%였다. 둘을 합치면 69.0%가 월 25만원 미만의 낮은 연금에 머물렀다. 당시의 연금은 많은 고령층에게 생활을 지탱하는 주된 소득이라기보다 보조적 현금흐름에 가까웠다.",
            "2025년에는 모습이 크게 달라진다. 10만원 미만은 0.2%, 10~25만원 미만은 4.0%로 줄고, 25~50만원 미만이 38.5%, 50~100만원 미만이 33.1%를 차지한다. 낮은 금액 구간이 빠르게 얇아지고 중간 구간이 두꺼워진 것이다. 100만원 이상 수령자 비중도 2008년 13.2%에서 2025년 24.3%로 높아졌다.",
            "그럼에도 이 그림의 결론은 낙관만은 아니다. 2025년에도 연금수령자의 71.6%는 월 25~100만원 구간에 있다. 이는 연금제도가 성숙하면서 저액 수령층을 줄였지만, 다수의 노후소득이 여전히 중간 이하 금액대에 집중되어 있음을 뜻한다. 노후빈곤 문제는 연금을 받느냐의 문제를 넘어, 받는 금액이 생활을 감당할 만큼 충분한가의 문제로 이동하고 있다.",
            "전문가의 관점에서 보면 이 분포 변화는 한국 노후소득 보장의 이중적 성격을 보여준다. 기초연금과 국민연금의 성숙은 낮은 수령액 구간을 줄이는 데 분명한 역할을 했다. 그러나 국민연금 가입 이력, 근로경력, 직역연금 여부, 사적연금 보유 여부가 서로 다르기 때문에 고령층 내부의 소득 격차는 쉽게 사라지지 않는다. 그래서 5.6절의 질문은 ‘평균이 올랐다’에서 멈추지 않고, ‘누가 여전히 낮은 구간에 남아 있는가’로 이어져야 한다."
        ],
    },
}


SECTION_NARRATIVE = {
    "section-1-1-age-structure.html": {
        "kicker": "인구구조를 읽는 첫 장면",
        "paragraphs": [
            "인구피라미드는 단순한 연령별 막대그래프가 아니다. 한 사회가 지나온 전쟁, 성장, 가족계획, 경제위기, 교육 확대, 수명 연장의 흔적이 한 화면에 겹쳐진 기록이다. 출산율이 낮아졌다는 말은 피라미드의 아래쪽이 좁아졌다는 뜻이고, 고령화가 진행된다는 말은 오래전에 태어난 큰 코호트가 위쪽으로 이동한다는 뜻이다.",
            "1980년, 1990년, 2020년, 2025년을 나란히 놓으면 변화는 더 분명해진다. 전후 베이비붐 세대는 시간이 흐르며 피라미드의 중심부에서 고령층으로 이동하고, 1997년 외환위기 이후 불안정해진 청년기의 삶은 이후 출생 코호트의 급격한 축소로 남는다. 이 절의 목적은 인구피라미드의 모양을 묘사하는 데 그치지 않고, 어느 세대가 왜 두껍고 어느 세대가 왜 얇은지 역사적 시간 속에서 읽는 데 있다.",
        ],
    },
    "section-1-2-population-measures.html": {
        "kicker": "인구라는 숫자는 하나가 아니다",
        "paragraphs": [
            "인구를 논할 때 가장 먼저 부딪히는 문제는 숫자가 하나가 아니라는 사실이다. 주민등록인구는 행정서비스의 대상자를 보여주고, 인구총조사는 실제 거주 실태를 더 가까이 포착하며, 인구동태의 연앙인구는 출생률과 사망률의 분모가 된다. 어느 숫자를 쓰느냐에 따라 같은 지역도 늘어나는 곳이 되거나 줄어드는 곳이 될 수 있다.",
            "따라서 이 절은 이후 분석의 방법론적 기준을 세우는 장이다. 저출산이나 고령화를 말하기 전에, 우리가 어떤 인구를 세고 있는지 밝혀야 한다. 정책의 대상, 재정 배분, 지방자치단체의 정원, 지역소멸 논의는 모두 이 기준 선택의 영향을 받는다.",
        ],
    },
    "section-2-1-yeonggwang-cohort.html": {
        "kicker": "전국 정책을 점검하는 지역 사례",
        "paragraphs": [
            "한국의 저출산 정책을 평가할 때 특정 지역의 높은 출산율이나 큰 출산장려금은 자주 성공 사례로 제시된다. 그러나 아이가 태어났다는 사실과 그 가족이 지역에 남았다는 사실은 같은 문장이 아니다. 이 절은 출산장려금을 적극적으로 운영하는 다섯 군을 골라, 출생연도 0세 인구가 4년 뒤 같은 지역의 4세 인구로 얼마나 남아 있는지 따라간다.",
            "이 점검은 정책을 더 차분하게 보게 만든다. 출생 직후의 현금지원은 출산 결정의 문턱을 낮출 수 있지만, 아이가 네 살이 될 때까지 가족을 붙잡는 힘은 주거, 일자리, 돌봄, 어린이집, 학교, 의료 접근성이 함께 만든다. 그래서 0세→4세 코호트 잔존율은 출산장려금의 단기 홍보 효과가 아니라 지역 생활 조건의 지속성을 묻는 지표다.",
            "패널 그림은 각 군마다 왼쪽에 조출생률, 오른쪽에 0세→4세 코호트 잔존율을 붙여 놓았다. 여기서 조출생률은 합계출산율이 아니라 해당 연도 출생아 수를 전체 인구로 나누어 1,000명당 몇 명이 태어났는지 보는 지표다. 예컨대 영광군은 2019-2020년에 조출생률이 10명대까지 높아졌지만, 같은 시기 출생 코호트의 4세 잔존율은 65-73% 수준으로 떨어진다. 해남군은 2013-2016년 조출생률이 높았지만 잔존율은 절반 안팎에 머문다. 반대로 고흥군은 조출생률 자체는 높지 않아도 2013-2018년 출생 코호트의 잔존율이 100% 안팎을 보이며 전입 효과가 코호트를 보강한다.",
            "2013-2020년 출생 코호트를 2017-2024년 4세 인구와 연결해 보면 평균 잔존율은 고흥군 96.08%, 진도군 93.17%, 영광군 81.20%, 강진군 70.11%, 해남군 57.82% 순으로 갈린다. 이 차이는 지급액의 크기만으로 설명되지 않는다. 어떤 지역에서는 다른 지역에서 들어오는 아이가 출생 코호트를 보강했고, 어떤 지역에서는 출생 이후 초등학교 입학 전까지 가족이 빠져나가는 흐름이 더 강했다.",
        ],
    },
    "section-2-2-fertility-conditions.html": {
        "kicker": "출산은 왜 뒤로 밀리는가",
        "paragraphs": [
            "한 세대 전에는 결혼, 첫 출산, 둘째 출산이 비교적 짧은 시간 안에서 이어졌다. 지금은 그 순서가 끊어지기보다 뒤로 밀린다. 학교를 마치고, 일자리를 얻고, 소득을 안정시키고, 집을 마련하고, 돌봄을 예측할 수 있는 시간이 늦게 온다.",
            "이 절은 출산율을 하나의 원인처럼 다루지 않는다. 연령별 출산율, 혼인 건수, 첫째·둘째 출산연령, 신혼부부 소득구간별 자녀 보유, 청년 고용 기반을 함께 놓고 출산 지연이 어떤 생활 조건의 조합으로 만들어지는지 따라간다.",
        ],
    },
    "section-3-1-regional-gap.html": {
        "kicker": "전국 평균 뒤의 다른 속도들",
        "paragraphs": [
            "한국의 인구문제는 전국 평균으로는 잘 보이지 않는다. 어떤 지역은 아직 완만하게 늙어가지만, 어떤 군 지역은 이미 주민 두 명 중 한 명 가까이가 65세 이상인 구조에 들어섰다. 평균은 이 차이를 지운다.",
            "지역 격차를 보려면 고령화율과 함께 청년 이동을 읽어야 한다. 노인이 많아서 고령화가 진행되는 것이 아니라, 청년과 가족 형성 연령층이 빠져나가면서 지역의 연령구조가 더 빠르게 늙는 경우가 많다. 그래서 이 장의 지도는 장식이 아니라, 학교·돌봄·의료·노동시장 압력이 어디서 먼저 나타나는지 보여주는 분석 도구다.",
        ],
    },
    "section-3-2-foreign-multicultural.html": {
        "kicker": "남는 사람과 새로 들어오는 사람",
        "paragraphs": [
            "지역 인구를 내국인 출생만으로 설명하는 시대는 이미 지나고 있다. 외국인 노동자, 유학생, 결혼이민자, 외국국적동포, 다문화 가족은 서로 다른 방식으로 지역사회에 들어오고 머문다. 이들은 단지 인구의 빈자리를 메우는 존재가 아니라, 지역 노동시장과 가족 형성의 구조 자체를 바꾼다.",
            "다문화 출생 비중이 높아진다는 것은 출생의 구성도 달라진다는 뜻이다. 출생아 수가 줄어드는 사회에서는 작은 비율 변화도 학교, 보육, 언어 지원, 지역사회 통합의 과제로 이어진다. 이 절은 외국인과 다문화를 주변적 주제가 아니라 지역 인구구조의 핵심 변수로 다룬다.",
        ],
    },
    "section-4-1-family-formation.html": {
        "kicker": "혼인이 줄면 출생도 흔들린다",
        "paragraphs": [
            "한국에서 출산은 여전히 혼인과 강하게 연결되어 있다. 그러므로 저출산을 말한다는 것은 곧 혼인의 감소, 혼인 연령의 상승, 이혼과 재혼, 혼외출생의 낮은 비중을 함께 읽는 일이다. 출산율만 보면 가족 형성의 제도적 통로가 어떻게 좁아졌는지 놓치기 쉽다.",
            "하지만 혼인을 늘리면 출생이 자동으로 늘어난다는 식의 결론은 성급하다. 혼인은 주거비, 일자리, 성평등한 돌봄, 지역의 생활 인프라가 일정 수준 이상 갖추어졌을 때 선택 가능한 제도가 된다. 이 절은 혼인과 출생의 상관을 확인하되, 그 관계를 떠받치는 조건을 함께 묻는다.",
        ],
    },
    "section-4-1-divorce-fear-marriage.html": {
        "kicker": "결혼은 약속이지만, 약속의 실패 가능성도 함께 상상된다",
        "paragraphs": [
            "결혼을 하지 않는 이유를 물으면 대개 돈, 주거, 일자리, 양육 부담이 먼저 나온다. 그러나 결혼은 경제계약만이 아니라 관계의 장기 약속이기도 하다. 그래서 어떤 사람에게 결혼의 부담은 ‘잘 살 수 있을까’가 아니라 ‘잘못되면 어떻게 될까’라는 두려움으로 나타난다.",
            "이 절은 이혼의 두려움이 결혼 회피의 핵심 원인이라고 단정하지 않는다. 대신 두 가지 자료를 나누어 본다. 하나는 30대와 40대의 실제 연령별 이혼율이고, 다른 하나는 사회가 이혼을 얼마나 수용하는지에 대한 인식이다. 실제 위험과 사회적 낙인이 함께 낮아지는지, 아니면 관계 실패에 대한 심리적 비용이 여전히 남아 있는지 따져본다.",
        ],
    },
    "section-4-2-men-care-parental-leave.html": {
        "kicker": "아빠가 육아를 하지 않는다는 말은 더 이상 그대로 맞지 않다",
        "paragraphs": [
            "한국의 저출산을 설명할 때 오래 반복된 문장이 있다. 아이를 낳아도 돌봄은 결국 여성에게 돌아간다는 말이다. 이 문장은 여전히 현실의 많은 부분을 설명한다. 그러나 최근의 육아휴직 통계를 보면 변화도 분명하다. 남성이 육아를 전혀 담당하지 않는 사회에서, 남성이 육아휴직 제도 안으로 빠르게 들어오는 사회로 이동하고 있다.",
            "e-나라지표 150401의 고용보험 DB 자료를 보면 육아휴직급여 수급자는 2017년 9만122명에서 2025년 18만4329명으로 두 배 이상 늘었다. 여성 수급자는 같은 기간 7만8080명에서 11만7129명으로 50.0% 증가했지만, 남성 수급자는 1만2042명에서 6만7200명으로 458.0% 증가했다. 그 결과 남성 비중은 2017년 13.4%에서 2025년 36.5%까지 올라왔다.",
            "이 변화는 태도의 변화와 제도의 변화가 함께 만든 결과다. 2014년 아빠육아휴직 보너스제, 2020년 부부 동시 육아휴직 허용, 2022년 부모 모두 육아휴직 사용 시 초기 급여를 높이는 제도 개편은 남성에게 ‘쉴 수 있는 권리’를 조금씩 현실화했다. 동시에 젊은 세대의 부부 관계에서는 돌봄을 여성의 일로만 보는 규범이 약해지고 있다. 통계는 이 문화적 변화를 완벽하게 설명하지는 못하지만, 적어도 남성의 제도 이용이 예외에서 흐름으로 바뀌고 있음을 보여준다.",
            "출산전후휴가급여 수급자도 함께 봐야 한다. 출산전후휴가급여 초회수급자는 2017년 8만1083명에서 2021년 7만275명까지 낮아졌다가 2025년 8만9574명으로 다시 늘었다. 같은 기간 지원금액은 2426억원에서 4101억원으로 증가했고, 1인당 지원금액은 299만원에서 458만원으로 높아졌다. 출산 자체가 줄어드는 시대에도 제도 단가는 커지고 있으며, 고용보험 안에 들어온 출산·육아 지원의 재정적 무게는 가벼워지지 않는다.",
            "육아휴직급여의 재정 규모는 더 빠르게 커졌다. 총 지원금액은 2017년 6804억원에서 2025년 3조6292억원으로 433.4% 증가했다. 이 지원금액을 육아휴직급여 초회수급자 수로 나눈 환산액은 2017년 755만원에서 2025년 1969만원으로 올랐다. 남성은 2017년 513만원에서 2025년 1599만원으로 늘었고, 여성은 792만원에서 2181만원으로 늘었다.",
            "여기서 중요한 것은 이 값을 개인별 실제 평균 수령액으로 단정하지 않는 일이다. 원표의 수급자 수는 ‘초회수급자 수’이고, 지원금액은 해당 연도 육아휴직급여 지원금액이다. 따라서 이 계산은 정확히 말하면 ‘연간 지원금액을 초회수급자 수로 나눈 환산액’이다. 그럼에도 남성과 여성의 차이는 해석할 만하다. 남성 수급자가 빠르게 늘었는데도 남성 환산액이 여성보다 낮다면, 남성이 육아휴직을 쓰기 시작했지만 여전히 더 짧게, 더 제한적으로 쓰고 있을 가능성이 크다. 반대로 여성의 환산액이 높은 것은 여성이 더 많은 돌봄 시간을 실제로 떠안고 있다는 신호로 읽을 수 있다.",
            "이 자료는 고용보험 DB에 잡히는 제도 이용자를 보여준다는 점도 잊지 말아야 한다. 육아휴직 통계는 임금노동자 내부의 변화를 잘 보여주지만, 자영업자, 플랫폼 노동자, 고용보험 밖의 불안정 노동자는 충분히 포착하지 못한다. 따라서 남성 육아휴직이 늘었다는 사실은 중요한 변화이지만, 그것만으로 모든 부모가 아이를 돌볼 시간을 얻었다고 말할 수는 없다. 제도의 중심이 정규직 임금노동자에게 먼저 열리고, 취약한 일자리에는 늦게 도달하는 문제가 남아 있다.",
            "그러므로 남성의 육아 태도 변화는 두 겹으로 읽어야 한다. 하나는 규범의 변화다. 아버지가 아이 돌봄에서 빠지는 것이 당연하다는 문화는 약해지고 있다. 다른 하나는 제도 이용의 불평등이다. 남성 육아휴직이 늘어도 회사에서 눈치를 보거나 승진·평가 불이익을 걱정한다면 실제 사용은 특정 직장과 계층에 집중된다. 숫자가 커졌다는 사실은 출발점이고, 누가 오래 쓸 수 있는지가 다음 질문이다.",
            "하지만 제도 이용만으로 남성의 실제 돌봄 참여를 판단하기는 어렵다. 그래서 생활시간조사를 함께 보아야 한다. 2024년 생활시간조사에서 미취학 자녀가 있는 가구의 남편은 하루 돌보기 시간이 2019년 1시간 2분에서 2024년 1시간 28분으로 늘었다. 같은 기간 아내도 3시간 13분에서 3시간 39분으로 늘었다. 남편의 증가폭은 26분으로 작지 않지만, 2024년에도 아내의 돌보기 시간은 남편의 약 2.5배다.",
            "부모의 돌보기 시간을 합쳐 보면 남편 비중은 2019년 24.3%에서 2024년 28.7%로 상승했다. 남성이 돌봄에서 완전히 빠져 있다는 말은 더 이상 맞지 않지만, 돌봄의 중심이 남성에게 옮겨 갔다고 말하기도 어렵다. 변화는 분명하지만 균형에는 아직 거리가 있다.",
            "18세 미만 자녀가 있는 맞벌이 가구에서도 비슷한 흐름이 보인다. 남편의 가사노동 시간은 2019년 1시간 11분에서 2024년 1시간 24분으로 늘었고, 아내는 3시간 49분에서 3시간 32분으로 줄었다. 남편 비중은 23.7%에서 28.4%로 올라갔다. 맞벌이 가구에서조차 아내의 가사노동 시간이 남편보다 훨씬 길지만, 격차가 조금씩 좁아지는 방향은 확인된다.",
            "따라서 정책적 시사점은 단순히 남성 육아휴직자 수가 늘었다는 데서 끝나지 않는다. 첫째, 남성 육아휴직은 이미 주변적 제도가 아니므로 기업 인사관리와 대체인력 지원, 승진 불이익 방지 장치를 실제로 작동시켜야 한다. 둘째, 급여 수준을 높이는 정책은 이용을 늘리지만 재정 지출도 빠르게 키우므로, 보편적 권리 확대와 지속 가능한 재원 설계를 함께 논의해야 한다. 셋째, 남성의 육아휴직이 짧은 ‘이벤트’가 아니라 일상적 돌봄 시간으로 이어지려면 장시간 노동 축소, 정시퇴근, 어린이집 등·하원 시간과 근무시간의 조정, 남성의 돌봄 사용에 대한 조직문화 개선까지 연결해 보아야 한다.",
        ],
    },
    "section-4-3-care-work-balance.html": {
        "kicker": "돌봄은 출산 이후의 문제가 아니다",
        "paragraphs": [
            "돌봄은 아이를 낳은 뒤에야 등장하는 사후 문제가 아니다. 보육시설의 접근성, 육아휴직의 실제 사용 가능성, 남성과 여성의 돌봄 분담은 아이를 낳을 수 있는 조건을 미리 결정한다. 출산 결정은 미래의 돌봄 시간을 상상하는 과정이기도 하다.",
            "보육아동수가 줄어드는 것은 단순히 수요가 감소했다는 뜻만은 아니다. 어린이집이 사라지고 돌봄 접근성이 낮아지면, 지역은 젊은 가족에게 더 머물기 어려운 곳이 된다. 따라서 돌봄 인프라의 축소는 저출산의 결과이면서 동시에 다음 저출산을 낳는 조건이 될 수 있다.",
        ],
    },
    "section-4-4-childcare-shortage.html": {
        "kicker": "가까운 어린이집은 출산의 배경조건이다",
        "paragraphs": [
            "아이를 낳을지 고민하는 사람은 출산 직후의 지원금만 계산하지 않는다. 복직할 수 있을지, 아이를 맡길 곳이 있는지, 등원 시간이 출근 시간과 맞는지, 갑자기 시설이 문을 닫지는 않을지까지 함께 생각한다. 이때 어린이집은 단순한 복지시설이 아니라 가족 형성을 가능하게 하는 생활 인프라가 된다.",
            "그래서 이 절은 어린이집 총량이 충분한가를 묻는 데서 멈추지 않는다. 어린이집 유형별 개소 수와 이용 아동 수를 함께 놓고, 민간·가정 어린이집의 축소와 국공립·직장 어린이집의 확대가 어떤 정책적 긴장을 만드는지 읽는다. 출생아 수 감소가 보육 수요를 줄이고, 보육 인프라 축소가 다시 출산 결정을 어렵게 만드는 순환을 확인하는 것이 이 절의 핵심이다.",
            "전국 총량만 보면 2024년 어린이집은 2만7387개소, 보육아동은 94만1303명이고 시설당 아동수는 34.4명이다. 2000년의 시설당 35.6명, 2014년의 34.2명과 크게 다르지 않다. 이 숫자만 보면 한국의 문제는 어린이집 정원이 절대적으로 부족하다는 결론으로 곧장 가지 않는다.",
            "그러나 유형별로 보면 이야기가 달라진다. 전체 어린이집 수는 2013년 4만3770개소로 정점을 찍은 뒤 2024년 2만7387개소로 줄었다. 특히 가정 어린이집은 2013년 2만3632개소에서 2024년 9586개소로, 민간 어린이집은 2014년 1만4822개소 정점 이후 2024년 8181개소로 줄었다. 반대로 국공립 어린이집은 2000년 1295개소에서 2024년 6521개소로 늘었고, 직장 어린이집도 204개소에서 1305개소로 커졌다.",
            "이용 아동 수에서도 같은 전환이 보인다. 전체 보육아동은 2014년 149만6671명으로 정점을 찍은 뒤 2024년 94만1303명으로 줄었다. 민간 어린이집 이용 아동은 2014년 77만5414명에서 2024년 37만3524명으로 거의 절반 수준이 되었고, 가정 어린이집 이용 아동은 2012년 37만1671명 정점에서 2024년 13만9172명으로 크게 줄었다. 그 사이 국공립 이용 아동은 2024년 29만3049명까지 늘어났다.",
            "정책적으로 중요한 대목은 여기다. 출생아 수가 줄면 시장 기반 시설부터 먼저 흔들린다. 민간·가정 어린이집이 줄어드는 것은 전국 차원에서는 수요 감소에 대한 조정처럼 보일 수 있지만, 어느 동네에서는 가장 가까운 보육 선택지가 사라지는 일이다. 국공립 확충은 질과 공공성을 높이는 방향이지만, 모든 생활권의 접근성 공백을 즉시 메우지는 못한다.",
            "따라서 ‘어린이집이 적어서 출산을 덜 한다’는 명제는 전국 시설 수의 부족이 아니라, 아이를 낳은 뒤 실제로 맡길 수 있는 가까운 시설이 있는가의 문제로 다시 써야 한다. 부모가 계산하는 것은 첫해 지원금만이 아니라 영아기부터 유아기까지 믿고 맡길 수 있는 시간표와 거리, 비용, 교사의 안정성이다. 보육 인프라가 빠르게 줄어드는 지역에서는 출산 감소가 시설 폐원을 낳고, 시설 폐원이 다시 출산과 정주 의향을 낮추는 순환이 생긴다.",
        ],
    },
    "section-4-5-household-housing.html": {
        "kicker": "사람은 줄어도 가구와 집은 다르게 움직인다",
        "paragraphs": [
            "인구가 감소하면 주택 수요도 곧바로 줄어들 것처럼 보인다. 그러나 현실은 더 복잡하다. 1인가구와 고령가구가 늘면 총인구가 정체하거나 감소해도 가구수는 한동안 늘 수 있고, 주거 수요는 지역별로 전혀 다른 방향을 보인다.",
            "빈집은 이런 시간차가 공간에 남긴 흔적이다. 빈집이 늘어난다는 것은 단순히 집이 남는다는 뜻이 아니라 학교, 상권, 의료, 교통이 함께 약해지는 생활권의 변화를 뜻한다. 이 절은 인구감소를 주거와 가구의 문제로 번역한다.",
        ],
    },
    "section-5-1-labor-aging.html": {
        "kicker": "고령층 노동은 예외가 아니라 구조가 되었다",
        "paragraphs": [
            "한국의 고령화는 노동시장 밖에서 벌어지는 인구 현상이 아니다. 55~79세 인구는 2010년 943만 명에서 2025년 1,645만 명으로 커졌고, 같은 기간 이 연령대의 경제활동인구는 487만 명에서 1,001만 명으로 늘었다. 취업자도 477만 명에서 978만 명으로 두 배가 넘게 증가했다. 숫자만 놓고 보면 ‘나이 든 사람이 더 많이 일한다’는 단순한 문장처럼 보이지만, 실제로는 은퇴의 경계가 뒤로 밀리고 노동시장 자체가 고령층을 전제로 재편되고 있다는 뜻이다.",
            "특히 55~64세는 이미 전통적 의미의 은퇴 직전 세대라기보다 핵심 노동력에 가깝다. 2025년 이들의 고용률은 71.1%로, 많은 사람이 여전히 사업장과 자영업 현장에 남아 있다. 반면 65~79세의 변화는 더 복합적이다. 취업자는 2010년 163만 명에서 2025년 379만 명으로 늘었고 고용률도 36.7%에서 47.2%로 올랐다. 이는 건강수명 연장과 숙련의 활용이라는 긍정적 측면을 갖지만, 동시에 공적연금과 노후소득이 충분하지 않아 일을 계속해야 하는 현실도 비춘다.",
            "실업자와 실업률은 이 흐름을 조금 다르게 보게 만든다. 55~79세 실업자는 2010년 10만5천 명에서 2025년 23만 명으로 늘었지만, 실업률은 2%대 초반에 머문다. 표면적으로는 실업 문제가 작아 보일 수 있다. 그러나 비경제활동인구가 456만 명에서 644만 명으로 커졌다는 사실을 함께 놓으면 이야기가 달라진다. 일자리를 찾는 사람만이 아니라, 건강, 돌봄, 구직 포기, 은퇴, 가사, 연금 수급 여부 때문에 노동시장 밖에 있는 사람까지 보아야 고령층의 실제 생활 조건이 보인다.",
            "이 절의 질문은 네 갈래로 나뉜다. 고령층에서 취업자는 얼마나 빠르게 증가하는가, 고용률은 얼마나 빠르게 올라가는가, 실업자는 얼마나 늘어나는가, 비경제활동인구는 얼마나 커지는가. 전국 자료는 한국 사회 전체의 방향을 보여주지만, 지역 자료는 그 변화가 어디에서 더 가파르게 진행되는지 보여준다. 그래서 시도별 자료에서는 60세 이상을 기준으로 연도를 독립변수로 둔 단순 회귀를 적용했다. 회귀계수는 각 지역에서 매년 취업자와 비경제활동인구가 몇 천 명씩 늘었는지, 고용률은 몇 퍼센트포인트씩 움직였는지 읽게 해 준다.",
            "따라서 고령층 취업 증가를 활력의 증거로만 읽어서도, 노인빈곤의 증거로만 읽어서도 부족하다. 정책적으로 중요한 질문은 ‘몇 명을 더 일하게 할 것인가’가 아니라, 어떤 사람에게는 괜찮은 일자리를 오래 열어 주고, 어떤 사람에게는 일을 멈출 수 있는 소득과 돌봄을 보장할 것인가이다. 고령사회 노동정책은 고용률을 올리는 기술이 아니라 은퇴, 재취업, 건강, 소득보장을 함께 설계하는 제도 문제가 된다.",
        ],
    },
    "section-5-3-lifecycle-fiscal.html": {
        "kicker": "마지막 질문은 누가 부담하는가이다",
        "paragraphs": [
            "인구구조 변화의 끝에는 재정과 생애주기 부담의 문제가 놓인다. 아이가 적어지고 노인이 많아진다는 말은 단지 인구 구성의 변화가 아니라, 누가 생산하고 누가 소비하며 누가 돌봄과 이전을 부담하는지의 변화다.",
            "국가채무나 재정지표는 이 문제의 배경선일 뿐이다. 더 중요한 질문은 연령별 노동소득과 소비가 어떻게 어긋나는지, 보건·돌봄·연금 지출이 어느 세대에 집중되는지, 청년과 아동에 대한 투자가 장기적으로 어떤 사회적 수익을 만드는지다. 이 절은 저출산·고령화를 세대 간 이전 구조의 문제로 마무리한다.",
        ],
    },
}


SECTION_READING_NOTE = {
    "section-1-1-age-structure.html": [
        "이 그림은 네 장의 가족사진처럼 읽으면 좋다. 1980년의 두꺼운 아래쪽은 아이와 청년이 많던 사회를 보여주고, 2025년의 좁아진 아래쪽은 앞으로 학교와 노동시장에 들어올 세대가 작아졌다는 뜻이다.",
        "특히 고령층에서 여성 막대가 더 길어지는 부분은 단순한 성비 차이가 아니다. 오래 사는 사람이 많아질수록 돌봄, 의료, 독거, 빈곤의 문제가 여성 고령층에게 더 무겁게 놓일 수 있음을 보여준다.",
    ],
    "section-1-2-population-measures.html": [
        "인구 통계가 서로 다르다는 말은 어느 한쪽이 틀렸다는 뜻이 아니다. 행정은 등록된 사람을 필요로 하고, 조사는 실제 거주를 확인하며, 출생률과 사망률은 연앙인구라는 계산용 분모를 쓴다.",
        "정책을 설계할 때 이 차이를 무시하면 지원 대상은 과대 또는 과소 계산된다. 그래서 이 절의 핵심은 숫자를 의심하자는 것이 아니라, 숫자가 쓰이는 자리를 정확히 보자는 데 있다.",
    ],
    "section-2-1-yeonggwang-cohort.html": [
        "각 군의 왼쪽 그림은 KOSIS 공식 항목명으로 조출생률이다. X축은 ‘출생년도’이며, 값은 해당 연도 전체 인구 천 명당 출생아 수다. 합계출산율처럼 여성 1명이 평생 낳을 것으로 예상되는 평균 자녀 수를 뜻하지 않는다.",
        "오른쪽 그림은 0세→4세 코호트 잔존율이다. X축은 역시 ‘출생년도’이지만, 괄호 안에 4세로 관측되는 연도, 즉 출생년도+4년을 함께 표시했다.",
        "오른쪽 선이 100%에 가까울수록 출생연도 0세 인구가 네 살이 될 때까지 지역에 비교적 많이 남았다는 뜻이다. 100%를 넘는 해는 해당 코호트가 줄지 않은 것이 아니라, 네 살이 되기 전 다른 지역에서 들어온 아이가 더해졌다는 뜻으로 읽어야 한다.",
        "반대로 잔존율이 낮은 지역은 출산장려금이 전혀 효과가 없었다고 단정하기보다, 출생 이후 가족이 머무를 조건이 충분했는지 물어야 한다. 정책의 시험대는 출생신고서가 아니라 아이가 어린이집과 학교로 넘어가는 생활의 시간이다.",
    ],
    "section-2-2-fertility-conditions.html": [
        "연령별 출산율을 보면 한국의 저출산은 단순히 아이를 덜 낳는 현상이 아니라, 아이를 낳는 시점이 뒤로 밀리고 둘째 이후로 이어질 시간이 짧아지는 현상임을 알 수 있다.",
        "첫째아 출산연령이 높아진다는 것은 개인의 선택 변화만을 뜻하지 않는다. 안정된 일자리, 살 집, 돌봄을 기대할 수 있는 시간이 늦게 찾아온다는 사회적 신호이기도 하다.",
    ],
    "section-3-1-regional-gap.html": [
        "청년 이동 자료는 인구감소가 어디서 시작되는지 보여준다. 출생아 수가 줄기 전에 먼저 지역을 떠나는 것은 대개 교육과 일자리, 주거 기회를 찾는 20대와 30대다.",
        "서울과 경기도의 순이동을 함께 보면 수도권도 하나의 공간이 아님을 알 수 있다. 서울은 진입의 장소이면서 동시에 가족 형성기에 밀려나는 장소가 되고, 경기도는 그 이동을 받아내는 주거지로 기능한다.",
    ],
    "section-3-2-foreign-multicultural.html": [
        "외국인과 다문화 출생은 저출산 논의의 주변부가 아니다. 아이가 줄어드는 사회에서 누가 지역에 들어와 일하고, 가족을 만들고, 학교와 마을의 구성원이 되는지는 인구정책의 중심 질문이 된다.",
        "다문화 출생 비중이 커진다는 것은 단지 출생 통계의 항목이 변한다는 뜻이 아니다. 보육, 교육, 언어, 지역사회 통합 정책이 출산정책과 따로 떨어져 있을 수 없다는 뜻이다.",
    ],
    "section-4-1-family-formation.html": [
        "출생, 혼인, 이혼, 사망을 한 그림에 놓으면 가족 형성의 배경이 보인다. 출생이 줄고 혼인이 줄어드는 동안 사망은 늘어나며, 자연증가가 약해지는 사회로 이동한다.",
        "이 흐름은 결혼을 장려하면 출생이 늘어난다는 단순한 결론으로 이어지지 않는다. 혼인이 가능한 생활 조건이 좁아졌기 때문에 출생도 함께 줄어든다는 쪽에 더 가깝다.",
    ],
    "section-4-1-divorce-fear-marriage.html": [
        "연령별 이혼율은 해당 연령 인구 천명당 이혼건수다. 이혼한 사람의 평균연령이 높아지면 30대 이혼율은 낮아지고 40대 이후 이혼율이 상대적으로 두꺼워질 수 있다.",
        "사회조사 이혼 인식은 ‘이혼을 권장하는가’가 아니라 ‘이혼을 사회적으로 받아들일 수 있는가’를 묻는 지표로 읽어야 한다. 수용도가 높아졌다고 해서 결혼의 위험 인식이 사라졌다는 뜻은 아니다.",
    ],
    "section-4-2-men-care-parental-leave.html": [
        "육아휴직급여 수급자 수의 남성 비중은 2017년 13.4%에서 2025년 36.5%로 높아졌다. 여전히 여성이 더 많이 쓰지만, 남성 이용은 더 이상 예외적 현상으로 보기 어렵다.",
        "성별 환산액은 육아휴직급여 지원금액을 초회수급자 수로 나눈 값이다. 개인별 실제 평균 수령액이 아니라 제도 지출 강도를 보여주는 지표로 읽어야 한다.",
        "생활시간조사의 시간은 제도 이용자가 아니라 실제 하루 행동을 측정한다. 육아휴직 통계가 제도 접근성을 보여준다면, 생활시간조사는 가정 안에서 돌봄이 어떻게 배분되는지 보여준다.",
        "출산전후휴가급여는 여성의 출산 전후 노동권을 보호하는 제도이고, 육아휴직급여는 아이가 태어난 뒤 부모의 돌봄 시간을 보전하는 제도다. 두 제도를 함께 보아야 출산과 돌봄의 비용이 어디에서 커지는지 보인다.",
    ],
    "section-4-3-care-work-balance.html": [
        "보육아동수가 줄어드는 것은 아이가 줄었다는 결과이지만, 어린이집 수가 함께 줄면 다음 세대의 부모에게는 더 큰 불안으로 돌아온다.",
        "돌봄 인프라는 한 번 사라지면 다시 세우기 어렵다. 그래서 보육 수요 감소를 단순히 예산 절감의 기회로 볼 것이 아니라, 지역이 가족을 붙잡을 능력이 약해지는 신호로 읽어야 한다.",
    ],
    "section-4-4-childcare-shortage.html": [
        "첫 번째 그림은 어린이집 유형별 개소 수다. 민간과 가정 어린이집이 줄어드는 동안 국공립과 직장 어린이집이 늘어나는지 보는 것이 핵심이다.",
        "두 번째 그림은 유형별 이용 아동 수다. 보육아동수 감소가 모든 유형에서 같은 속도로 나타나는지, 아니면 민간·가정 시설에 더 크게 집중되는지 비교한다.",
        "세 번째 그림은 전체 시설 수, 전체 보육아동수, 시설당 아동수를 함께 보여준다. 시설당 아동수가 크게 나빠지지 않아도, 생활권 단위에서는 가까운 어린이집이 사라질 수 있다는 점을 함께 읽어야 한다.",
    ],
    "section-4-5-household-housing.html": [
        "인구가 줄어도 가구가 바로 줄지 않는 이유는 삶의 단위가 바뀌기 때문이다. 혼자 사는 사람과 고령가구가 늘면 같은 인구라도 필요한 집의 수와 형태는 달라진다.",
        "빈집은 이 변화가 지역 공간에 남긴 흔적이다. 사람이 떠난 집이 늘어나는 곳에서는 학교, 상권, 병원, 대중교통도 함께 약해질 가능성이 크다.",
    ],
    "section-5-1-labor-aging.html": [
        "각 패널은 같은 DT_1DE8031S 표에서 나온 매년 5월 값이다. 고령층인구, 경제활동인구, 취업자, 실업자, 비경제활동인구는 천명 단위이고, 고용률과 실업률은 퍼센트 단위다.",
        "55~79세 전체 선은 고령층 노동시장의 총량을 보여준다. 55~64세 선은 정년 전후의 ‘연장된 중년 노동시장’을, 65~79세 선은 제도상 은퇴 이후에도 계속되는 ‘노후 노동시장’을 보여준다.",
        "취업자와 고용률만 보면 고령층 노동 확대가 선명하지만, 비경제활동인구도 함께 늘어난다. 이 절의 핵심은 고령층을 하나의 집단으로 보지 않고, 일할 수 있고 일하고 싶은 사람, 일해야만 하는 사람, 일을 멈춰야 하는 사람을 구분해 읽는 것이다.",
        "지역별 회귀분석은 전국 고령층 부가조사와 연령 범주가 완전히 같지 않다. KOSIS 시도별 경제활동인구조사에서 공통으로 제공되는 60세 이상을 사용했으며, 회귀계수는 인과효과가 아니라 2010-2025년 사이 지역별 변화 속도를 요약한 값이다.",
    ],
    "section-5-2-aging-index.html": [
        "노령화지수의 기준선은 100이다. 100보다 작으면 유소년 인구가 고령 인구보다 많고, 100보다 크면 고령 인구가 유소년 인구보다 많다는 뜻이다.",
        "노령화지수는 고령화율보다 더 민감하게 움직인다. 분자는 고령 인구 증가, 분모는 유소년 인구 감소이기 때문에 저출산과 고령화가 동시에 진행될 때 지수는 빠르게 상승한다.",
        "이 지수의 상승은 학교와 보육시설의 축소, 고령층 돌봄과 의료 수요 증가, 노동시장 참여 연령의 상향, 연금과 재정 부담 증가를 한 흐름으로 이어 주는 배경 지표다.",
    ],
    "section-5-3-lifecycle-fiscal.html": [
        "재정 지표는 인구문제의 끝에 놓인 질문을 보여준다. 누가 일하고, 누가 돌봄을 받고, 누가 비용을 내는가가 세대별로 달라지기 때문이다.",
        "고령화와 국가채무를 같은 축에서 보면 단순히 돈이 부족하다는 이야기가 아니다. 한 사회가 줄어드는 아이, 늙어가는 인구, 길어지는 노후를 어떤 순서와 기준으로 책임질 것인가의 문제다.",
    ],
    "section-5-3-health-spending-aging.html": [
        "이 그림의 X축은 연령이고, 85세 이상은 하나의 열린 구간으로 묶어 85에 표시했다. Y축은 국민이전계정의 1인 공공보건소비를 백만원 단위로 바꾼 값이다.",
        "선이 위로 이동했다는 것은 같은 나이에서도 공공보건 지출이 늘었다는 뜻이다. 고령층 인구가 늘어나는 효과까지 더하면 실제 총재정 압력은 이 그림보다 더 커진다.",
    ],
    "section-5-4-aging-budget.html": [
        "막대는 예산 금액이고 선은 세부사업 수다. 두 값이 같은 방향으로 움직이지 않는다는 점이 중요하다. 사업 수가 줄어도 예산은 늘 수 있고, 그때 재정 압력은 ‘많은 사업’이 아니라 ‘큰 제도’에서 나온다.",
        "기초연금 계열은 2008년 기초노령연금으로 시작해 2014년 기초연금 도입 이후 급격히 커진다. 이 변화는 단순한 복지사업 신설이 아니라 고령 인구 전체를 대상으로 하는 현금급여가 재정의 중심축이 되는 과정이다.",
        "이 분석은 사업명 키워드 방식이므로 고령층에게 간접적으로 영향을 주는 의료·주거·교통 예산을 모두 포괄하지는 않는다. 대신 ‘이름에서부터 노인·고령화 정책으로 식별되는 예산’이 얼마나 커졌는지 보수적으로 확인하는 지표로 읽어야 한다.",
    ],
    "section-5-5-elderly-pension.html": [
        "왼쪽 축은 월평균 연금수령액이고 오른쪽 축은 연금수령률이다. 평균수령액은 연금을 받는 사람만을 대상으로 한 값이며, 연금수령률은 55~79세 전체 중 연금수령자의 비율이다.",
        "남녀 선의 간격을 주의해서 봐야 한다. 여성의 수령액 증가율은 높지만 출발점이 낮았고, 2025년에도 평균 수령액은 남성보다 훨씬 낮다. 노년기의 소득 격차는 노년기에 갑자기 생기는 것이 아니라 청장년기의 노동시장 이력이 누적된 결과다.",
    ],
    "section-5-6-elderly-pension-distribution.html": [
        "이 그림은 평균수령액이 아니라 연금수령자 내부의 분포를 보여준다. 각 막대는 해당 연도 연금수령자 100명 중 몇 명이 어느 월수령액 구간에 있는지를 뜻한다.",
        "2008년과 2025년을 비교하면 낮은 금액 구간이 급격히 줄고 25만원 이상 구간이 두꺼워진다. 그러나 2025년에도 중심은 25~100만원 구간에 있다. 연금의 양적 확대가 곧 충분한 노후소득으로 이어지는 것은 아니다.",
        "100만원 이상 구간이 늘어난 것도 중요하다. 연금제도의 성숙은 고액 수령층을 키우지만, 동시에 가입 이력과 노동시장 경력의 차이를 노년기 소득 격차로 남긴다. 이 그림은 노후소득 정책이 평균이 아니라 분포를 보아야 하는 이유를 보여준다.",
    ],
}


SECTION_DATA_EXPANSION = {
    "section-6-1-education-cost-fertility.html": [
        {
            "question": "사교육비는 실제로 줄고 있는가, 아니면 학생 수 감소 속에서도 1인당 부담이 커지고 있는가?",
            "data": "KOSIS DT_1PE003 사교육비 총액, DT_1PE201 전체학생 1인당 월평균 사교육비, DT_1PE301 사교육 참여율",
            "files": ["data/education_DT_1PE003.csv", "data/education_DT_1PE201.csv", "data/education_DT_1PE301.csv", "data/derived/private_education_cost_trend.csv"],
            "analysis": "사교육비 총액은 조원, 월평균 사교육비는 만원, 참여율은 퍼센트로 정리하고 2007년 이후 추세와 2025년 변화를 함께 비교한다.",
            "interpretation": "출산 결정에서 중요한 것은 현재 지출액만이 아니라 아이 한 명을 낳으면 장기간 교육경쟁 비용을 떠안는다는 예상이다.",
        }
    ],
    "section-6-2-private-education-by-school-level.html": [
        {
            "question": "사교육 경쟁은 대학입시 직전에 시작되는가, 아니면 초등 단계부터 이미 일상화되어 있는가?",
            "data": "KOSIS DT_1PE201 학교급별 1인당 월평균 사교육비, DT_1PE301 학교급별 사교육 참여율",
            "files": ["data/education_DT_1PE201.csv", "data/education_DT_1PE301.csv", "data/derived/private_education_school_level.csv"],
            "analysis": "초등학교, 중학교, 고등학교의 월평균 사교육비와 참여율을 같은 연도 축에서 비교한다.",
            "interpretation": "초등학교 단계부터 높은 참여율이 나타난다면 교육비 부담은 입시비용이 아니라 양육 전 과정의 비용으로 작동한다.",
        },
        {
            "question": "고등학생의 사교육 참여율은 왜 2020년 이후 2024년까지 빠르게 올랐는가?",
            "data": "KOSIS DT_1PE301 학교급별 사교육 참여율, 2023·2024·2025년 초중고사교육비조사 결과, 교육부 사교육 경감대책·2028 대입제도 개편안",
            "files": ["data/education_DT_1PE301.csv", "data/derived/high_school_private_education_drivers.csv"],
            "analysis": "고등학교 전체 참여율과 일반교과, 국어·영어·수학·사회/과학, 유료인터넷 강좌, 진로·진학 학습상담 참여율을 2019-2025년으로 분리해 비교한다.",
            "interpretation": "고등학생 사교육 증가는 입시 직전의 한 과목 문제가 아니라 수능·내신·학생부·진학상담 불안이 동시에 커진 결과다. 다만 2025년에는 전체 참여율이 내려가므로 2024년까지의 상승과 최신 하락을 구분해 읽어야 한다.",
        }
    ],
    "section-6-3-education-cost-inequality.html": [
        {
            "question": "교육비 부담은 모든 가구에 같은가, 아니면 계층별로 전혀 다른 교육경쟁을 만들고 있는가?",
            "data": "KOSIS DT_1PE209 가구소득별 1인당 월평균 사교육비, DT_1PE309 가구소득별 사교육 참여율",
            "files": ["data/education_DT_1PE209.csv", "data/education_DT_1PE309.csv", "data/derived/private_education_income_gap.csv"],
            "analysis": "2025년 소득구간별 지출액과 참여율을 비교하고, 저소득·고소득 구간의 격차를 계산한다.",
            "interpretation": "사교육비는 단순 소비가 아니라 자녀의 미래 지위를 둘러싼 방어적 투자로 작동하며, 이 격차가 둘째·셋째 출산의 기대 비용을 키운다.",
        },
        {
            "question": "소득이 높은 가구는 사교육비를 많이 쓰는데, 그렇다면 출산율은 더 낮은가?",
            "data": "KOSIS DT_1NW2016 초혼 신혼부부의 소득(근로·사업소득) 구간별 출산자녀 현황",
            "files": ["data/kosis_newlywed_income_children_DT_1NW2016.csv", "data/derived/newlywed_income_fertility.csv"],
            "analysis": "2015-2024년 초혼 신혼부부를 연간 근로·사업소득 구간별로 나누고, 무자녀 비중과 평균 출생아 수를 비교한다.",
            "interpretation": "결혼 초기에는 소득이 가장 높은 구간에서 평균 출생아 수가 낮고 무자녀 비중이 높다. 다만 이는 평생 출산율이 낮다는 뜻이 아니라 고소득 맞벌이·주거·경력비용 때문에 출산 시점이 늦어지는 효과를 함께 반영한다.",
        }
    ],
    "section-6-4-school-age-decline-education.html": [
        {
            "question": "학생 수가 줄면 교육비 부담도 자연스럽게 줄어드는가?",
            "data": "KOSIS 장래인구추계 0-14세 인구 추산치, 초중고사교육비조사 사교육비 총액·1인당 비용·참여율",
            "files": ["data/population_projection_indicators.csv", "data/education_DT_1PE003.csv", "data/education_DT_1PE201.csv", "data/education_DT_1PE301.csv", "data/derived/school_age_private_education_pressure.csv"],
            "analysis": "0-14세 인구, 사교육비 총액, 1인당 월평균 사교육비, 참여율을 2007년=100 지수로 바꾸어 비교한다.",
            "interpretation": "아이 수 감소가 경쟁 완화로 자동 전환되지 않는다면, 저출산은 교육비 문제를 줄이는 것이 아니라 더 적은 아이에게 더 많은 투자가 몰리는 구조를 만들 수 있다.",
        }
    ],
    "section-6-5-education-expectation-burden.html": [
        {
            "question": "부모는 왜 자녀 교육을 대학까지 책임져야 한다고 느끼는가?",
            "data": "KOSIS DT_1SSED100R 자녀 교육비 부담 인식, DT_1SSED110R 가장 부담되는 자녀 교육비 항목, DT_1SSED080R 부모가 기대하는 자녀 교육수준",
            "files": ["data/education_DT_1SSED100R.csv", "data/education_DT_1SSED110R.csv", "data/education_DT_1SSED080R.csv", "data/derived/education_burden_perception.csv"],
            "analysis": "학생 자녀가 있는 가구의 교육비 부담 인식과 부담 항목, 부모가 기대하는 자녀 교육수준을 격년 추세로 정리한다.",
            "interpretation": "대학 진학이 예외가 아니라 기본값이 되는 사회에서는 출산이 단기 양육비가 아니라 장기 교육비 약속으로 받아들여진다.",
        }
    ],
    "section-1-1-age-structure.html": [
        {
            "question": "피라미드의 움푹 들어간 연령대는 어느 세대인가?",
            "data": "KOSIS DT_1BPA001 성·연령별 1세별 추계인구, 1980·1990·2020·2025년",
            "files": ["data/derived/population_pyramid_5yr_1980_1990_2020_2025.csv"],
            "analysis": "KOSIS가 제공하는 중위추계 5세 연령군을 사용해 좌우 피라미드를 그리고, 특정 연령대의 돌출·침식을 출생연도 코호트로 환산한다.",
            "interpretation": "한국전쟁, 전후 베이비붐, 가족계획, 외환위기 이후 가족 형성 지연, 2015년 이후 출생 급감이 연령층의 두께로 남는다.",
        },
        {
            "question": "가족 형성 핵심 연령층과 학령인구는 함께 줄고 있는가?",
            "data": "KOSIS 장래인구추계의 0-14세, 15-64세, 65세 이상 구성비와 1세별 피라미드 원자료",
            "files": ["data/derived/age_composition_projection.csv", "data/population_projection_indicators.csv"],
            "analysis": "20-39세, 6-11세, 65세 이상을 별도 집계해 피라미드 변화와 학교·노동시장 수요 변화를 연결한다.",
            "interpretation": "저출산은 출생아 수 문제가 아니라 교육, 노동, 돌봄 수요의 순차적 축소로 이동한다.",
        },
    ],
    "section-1-2-population-measures.html": [
        {
            "question": "주민등록인구, 장래추계, 인구총조사는 무엇을 다르게 보는가?",
            "data": "KOSIS DT_1B040A3 주민등록인구현황, DT_1IN1502 인구총조사 총인구, DT_1BPB002 장래인구추계",
            "files": ["data/derived/population_measure_comparison.csv", "data/population_measure_comparison.csv", "data/population_projection_indicators.csv"],
            "analysis": "2000-2024년 전국 기준으로 주민등록인구, 인구총조사 총인구, 장래인구추계 중위추계를 같은 축에 놓고 차이를 계산한다. 총조사는 2000·2005·2010년 전수조사 값과 2015년 이후 등록센서스 연간 값을 연결한다.",
            "interpretation": "정책 대상 규모를 계산할 때는 행정등록 기준, 국내 상주 기준, 분석·전망 기준을 구분해야 한다.",
        },
        {
            "question": "인구가 줄어드는가, 아니면 특정 지역에 더 몰리는가?",
            "data": "KOSIS 시군구 주민등록인구와 2024년 시군구 고령화율",
            "files": ["data/sigungu_aging_2024.csv", "map_data.js"],
            "analysis": "시군구별 인구 집중도, 상위·하위 분위, 고령화율 지도를 함께 만든다.",
            "interpretation": "전국 감소보다 중요한 것은 감소와 집중이 동시에 진행되는 공간 구조다.",
        },
    ],
    "section-1-3-2010-registration-jump.html": [
        {
            "question": "2010년 주민등록인구 증가는 실제 인구 증가였는가, 통계 기준의 변화였는가?",
            "data": "KOSIS DT_1B040A3 주민등록인구현황, 행정안전부 거주불명등록 제도 보도자료",
            "files": ["data/derived/resident_registration_2010_jump.csv", "data/population_measure_comparison.csv"],
            "analysis": "전국 주민등록인구의 전년 대비 증가분을 계산하고 2010년 증가분을 주변 연도와 비교한다.",
            "interpretation": "2010년의 큰 증가는 출생·사망·이동의 순수한 결과라기보다 거주불명등록자 포함이라는 행정 기준 변화가 만든 시계열 단절이다.",
        },
        {
            "question": "100세 이상 인구는 왜 고령화보다 더 민감하게 움직이는가?",
            "data": "KOSIS DT_1B04006 전국 1세별 주민등록인구, 2008-2025년",
            "files": ["data/resident_registration_national_age_DT_1B04006.csv", "data/derived/resident_registration_centenarian_trend.csv"],
            "analysis": "전국 주민등록인구 중 100세 이상 인구와 전체 인구 10만 명당 100세 이상 인구를 계산한다.",
            "interpretation": "100세 이상 인구는 장수 증가의 신호이면서 동시에 거주불명자 정리와 말소 기준 변화에 취약한 행정통계의 민감한 구간이다.",
        },
    ],
    "section-2-1-population-growth-regions.html": [
        {
            "question": "지난 20년 동안 인구가 증가한 시군구는 어디인가?",
            "data": "KOSIS DT_1B040A3 행정구역(시군구)별 성별 주민등록인구수, 2004-2024년",
            "files": [
                "data/sigungu_population_2004_2024.csv",
                "data/derived/sigungu_population_trend_slopes.csv",
                "data/derived/sigungu_population_trend_map_values.csv",
                "data/geo/skorea-municipalities-2018-topo-simple.json",
            ],
            "analysis": "시군구별 주민등록인구를 종속변수, 연도를 독립변수로 둔 단순회귀를 추정하고 연도 계수의 크기를 지도에 표시한다.",
            "interpretation": "전국 인구 감소는 모든 지역의 동시 감소가 아니라 성장축과 축소축의 동시 진행을 뜻한다.",
        }
    ],
    "section-2-2-population-concentration.html": [
        {
            "question": "거점별 인구 집중도는 실제로 심화되고 있는가?",
            "data": "KOSIS DT_1B040A3 행정구역(시군구)별 성별 주민등록인구수, 2004-2024년",
            "files": [
                "data/derived/sigungu_population_concentration.csv",
                "data/derived/sigungu_population_concentration_indices.csv",
                "data/derived/sigungu_population_top_growth_hubs.csv",
                "data/derived/sigungu_population_rank_snapshots.csv",
            ],
            "analysis": "시군구 인구를 하위 행정단위 기준으로 정리한 뒤 상위 10·20·50개 지역 비중, 수도권 비중, 성장거점 20개 지역 비중, 지니계수, HHI, 유효 지역 수를 연도별로 계산한다.",
            "interpretation": "전국 상위 시군구 비중은 급격히 뛰지는 않지만, 수도권과 성장거점 20개 지역의 비중은 뚜렷하게 커져 인구 집중은 특정 성장축 중심으로 진행된다.",
        }
    ],
    "section-2-5-international-low-fertility.html": [
        {
            "question": "저출산은 한국만의 문제인가?",
            "data": "World Bank 합계출산율, 대만 공식 성별지표 플랫폼, OECD Family Database, Eurostat 모친 출생국별 출생 자료",
            "files": [
                "data/derived/international_tfr_trends.csv",
                "data/derived/fertility_family_structure_comparison.csv",
                "data/worldbank_tfr_selected_countries.csv",
                "data/eurostat_foreign_born_mother_births_2023.csv",
            ],
            "analysis": "한국·일본·대만·싱가포르와 유럽 주요국의 합계출산율 추세를 비교하고, 비혼 출산 비중과 외국 출생 모친 출생 비중을 함께 놓는다.",
            "interpretation": "동아시아 저출산은 결혼 중심 출산규범과 높은 양육·교육·주거비, 성별 돌봄 불평등이 결합된 현상이며, 유럽의 이민자 출산과 비혼 출산은 출산율 하락을 완충하지만 그 자체로 대체수준을 회복시키지는 못한다.",
        }
    ],
    "section-2-0-international-policy-success.html": [
        {
            "question": "저출산 정책이 성공한 나라는 있는가?",
            "data": "World Bank 합계출산율, 통계청 2024 출생·사망통계, SingStat Births and Fertility, Hungary KSH STADAT, Eurostat demo_find, 일본 후생노동성 인구동태통계, 각국 공식 가족정책 자료",
            "files": ["data/derived/pronatalist_policy_country_comparison.csv", "data/worldbank_tfr_selected_countries.csv"],
            "analysis": "한국·싱가포르·헝가리·일본의 대표 정책수단을 현금·세제, 주거, 돌봄·휴직, 구조개혁 유형으로 요약하고, 정책 강화 이후 합계출산율의 시작점·정점·최근값을 비교한다.",
            "interpretation": "헝가리는 일정한 반등을 보였지만 지속성과 포괄성에 한계가 있고, 싱가포르와 일본은 강한 제도에도 초저출산을 되돌리지 못했다. 한국의 과제는 제도 이름을 수입하는 것이 아니라 청년의 생활시간표를 실제로 바꾸는 조건을 만드는 것이다.",
        }
    ],
    "section-2-1-housing-support-marriage-birth.html": [
        {
            "question": "주거지원 정책은 어떤 방식으로 결혼과 출산을 늘리려 하는가?",
            "data": "국토교통부 2025년 업무계획, 저출산고령사회위원회 주거정책 보도자료, 국회예산정책처 2026년도 예산안 총괄 분석",
            "files": ["data/derived/housing_support_policy_budget.csv", "data/derived/low_fertility_major_budget_2026.csv"],
            "analysis": "저출생 대응 주요사업 중 주거 분야 예산을 2025년과 2026년으로 비교하고, 공급·청약·대출·거주기간 연장·지자체 임대료 지원으로 정책수단을 분류한다.",
            "interpretation": "주거지원은 출산 이후 보상보다 결혼과 첫 출산 이전의 고정비와 불확실성을 낮추는 정책수단으로 설계되어야 한다.",
        },
        {
            "question": "주거 안정성이 높아지면 혼인과 출산도 함께 높아지는가?",
            "data": "KOSIS DT_1OH0403·DT_1OH0418 40세 미만 가구주 주택소유·무주택 가구, DT_1B8000I 조혼인율·조출생률",
            "files": ["data/derived/housing_security_outcomes_national.csv", "data/derived/housing_security_vital_sido_panel.csv"],
            "analysis": "전국과 시도 패널에서 40세 미만 가구주의 주택보유율, 조혼인율, 조출생률의 2015-2024년 추세를 결합한다.",
            "interpretation": "전국적으로는 40세 미만 주택보유율이 낮아지는 동안 혼인과 출생도 장기 하락했다. 다만 2024년 혼인 반등은 주거정책만으로 설명할 수 없으므로 경기순환, 코로나19 이후 이연 혼인, 제도 변화 기대를 함께 보아야 한다.",
        },
        {
            "question": "공공주택 지원은 청년·신혼 가구의 실제 주거 경로를 바꾸고 있는가?",
            "data": "주택금융공사 주택금융 및 보금자리론 실태조사 DT_KHFC_026 점유형태, KOSIS 40세 미만 가구주 주택소유 자료",
            "files": ["data/derived/housing_tenure_young_newlywed.csv", "data/derived/housing_security_outcomes_national.csv"],
            "analysis": "30대 이하·신혼·미혼 가구의 자가, 전세, 보증금 있는 월세 비중을 비교해 공공주택과 주거지원이 겨냥하는 불안정한 초기 주거 경로를 확인한다.",
            "interpretation": "공공주택 효과는 공급량 자체가 아니라 전세·월세 의존을 낮추고 혼인·출산기의 거주 안정성을 높였는지로 평가되어야 한다.",
        },
        {
            "question": "전세·구입자금 대출은 부담을 낮추는가, 아니면 부채를 뒤로 미루는가?",
            "data": "KOSIS DT_1HDAAA06 가구주연령계층별 자산·부채·소득 현황",
            "files": ["data/derived/housing_finance_burden_by_age.csv"],
            "analysis": "29세 이하와 30~39세 가구주 가구의 부채/처분가능소득, 원리금상환액/처분가능소득, 현거주지 전월세보증금/처분가능소득 비율을 계산한다.",
            "interpretation": "정책대출은 초기 진입장벽을 낮추지만 청년·30대 가구의 부채와 상환부담이 이미 높다면 출산 위험을 줄이기보다 미래 소득을 미리 당겨 쓰게 만들 수 있다.",
        },
        {
            "question": "청년·신혼부부 주거지원은 일상 생활비 압력을 완화했는가?",
            "data": "청년 프로젝트 보조 정리자료의 가계소비 중 주거비 비중",
            "files": ["data/derived/youth_housing_consumption_pressure.csv"],
            "analysis": "2010년 이후 가계소비에서 주거비가 차지하는 비중의 장기 변화를 확인해 체감 주거 부담이 완화되었는지 검토한다.",
            "interpretation": "지원제도가 확대되어도 생활비 안에서 주거비 비중이 내려가지 않는다면 정책은 혼인·출산의 심리적 안전판으로 충분히 작동하지 못한다.",
        },
        {
            "question": "주거지원이 강하면 출산율은 자동으로 높아지는가?",
            "data": "싱가포르·프랑스·이스라엘의 공식 합계출산율과 OECD 주거가격·공공주택 관련 자료",
            "files": ["data/derived/international_housing_fertility_cases.csv"],
            "analysis": "공공주택 비중이 높은 싱가포르, 주거비가 높지만 출산율이 높은 이스라엘, 가족정책과 주거수당이 결합된 프랑스를 한국과 비교한다.",
            "interpretation": "국제 사례는 주거지원의 핵심이 집값 보조 자체가 아니라 출산 이후에도 유지되는 생활권, 돌봄, 시간, 노동시장 안정과 결합되는 데 있음을 보여준다.",
        },
        {
            "question": "수도권에서는 주거 안정성과 가족 형성의 관계가 더 뚜렷한가?",
            "data": "서울·인천·경기의 40세 미만 가구주 주택보유율, 조혼인율, 조출생률",
            "files": ["data/derived/capital_region_housing_marriage_birth.csv", "data/derived/housing_security_outcome_regression.csv"],
            "analysis": "서울·인천·경기만 따로 분리해 추세를 그리고, 시도-연도 패널에서 연도 추세를 통제한 단순 회귀계수를 비교한다.",
            "interpretation": "수도권에서는 주택보유율과 조출생률의 양의 관계가 상대적으로 더 분명하지만, 조혼인율은 단순히 주택보유율만으로 설명되지 않는다. 서울의 낮은 주택보유율과 높은 일자리 접근성, 경기의 주거 수용지 역할을 함께 읽어야 한다.",
        },
    ],
    "section-2-1-yeonggwang-cohort.html": [
        {
            "question": "조출생률이 높아진 해의 아이들은 네 살까지 지역에 남는가?",
            "data": "KOSIS 시군구 조출생률과 지역 1세별 주민등록인구, 영광군·강진군·고흥군·해남군·진도군의 출생연도별 0세·4세 코호트",
            "files": ["data/derived/birth_incentive_region_panel_cbr_retention.csv", "data/derived/birth_incentive_region_birth_rate_validation.csv", "data/kosis_birth_incentive_crude_birth_rate.csv", "data/kosis_birth_incentive_regions_age.csv"],
            "analysis": "출생연도별 조출생률과 birth_year = year - age 방식으로 재구성한 0세→4세 잔존율을 같은 X축에 놓고 각 군별 좌우 패널로 비교한다. 조출생률은 KOSIS T11 공식값이며, 검증표에는 T10 출생건수와 T11에서 역산되는 분모를 함께 남겼다.",
            "interpretation": "조출생률 상승이 지역 내 코호트 유지로 이어졌는지를 따로 점검해야 한다. 100% 초과는 코호트 유지가 아니라 전입을 포함한 순증으로 해석한다.",
        },
        {
            "question": "다섯 군의 평균 잔존율은 얼마나 다르게 나타나는가?",
            "data": "2013-2020년 8개 출생 코호트의 시군구별 평균 0세·4세 인구와 평균 잔존율",
            "files": ["data/derived/birth_incentive_region_cohort_summary.csv"],
            "analysis": "시군구별 8개 코호트 평균을 계산해 출생 규모와 4세 잔존 규모, 평균 잔존율, 평균 감소율을 비교한다.",
            "interpretation": "같은 전남 군 지역이고 현금성 출산지원이 있어도 잔존율은 크게 갈린다. 정책 평가는 지급액보다 가족이 계속 살 수 있는 조건을 함께 보아야 한다.",
        },
    ],
    "section-2-2-fertility-conditions.html": [
        {
            "question": "출산 지연은 어느 연령대에서 먼저 나타나는가?",
            "data": "KOSIS 연령별 출산율과 출산순위별 평균 출산연령",
            "files": ["data/derived/fertility_age_pattern.csv", "data/derived/mean_birth_age_order.csv"],
            "analysis": "25-29세, 30-34세, 35-39세 출산율과 첫째·둘째아 평균 출산연령을 함께 읽어 출산 시점 이동을 확인한다.",
            "interpretation": "첫째아 출산이 뒤로 밀리면 둘째 이상 출산으로 이어질 시간도 줄어든다. 출산율 하락은 출산 포기와 출산 지연이 결합된 결과다.",
        },
        {
            "question": "혼인과 소득, 고용 기반은 출산 시점과 어떻게 연결되는가?",
            "data": "KOSIS 인구동태 혼인·출생 건수, 초혼 신혼부부 소득구간별 자녀 현황, e-나라지표 청년 고용동향",
            "files": ["data/derived/vital_events_policy.csv", "data/derived/newlywed_income_fertility.csv", "data/derived/youth_employment_context.csv"],
            "analysis": "혼인 건수의 장기 감소, 신혼부부 소득구간별 무자녀 비중과 평균 출생아 수, 청년 고용 기반 변화를 연결해 출산 지연의 생활 조건을 해석한다.",
            "interpretation": "한국에서는 혼인이 출산의 주요 통로이고, 소득은 고용 안정의 결과다. 따라서 출산 지연은 혼인 지연, 일자리 안정, 소득 형성, 주거·돌봄 기대가 동시에 늦어지는 과정으로 이해해야 한다.",
        },
    ],
    "section-3-0-living-population.html": [
        {
            "question": "주민등록인구가 적은 지역은 실제 생활 수요도 작은가?",
            "data": "행정안전부·통계청 2025년 3분기 인구감소지역 생활인구 산정 결과",
            "files": [
                "data/source/living_population_2025q3_status.xlsx",
                "data/source/living_population_2025q3_stay_population.xlsx",
                "data/derived/living_population_2025q3_summary.csv",
                "data/derived/living_population_2025q3_map_values.csv",
                "data/derived/living_population_2025q3_age_component.csv",
                "data/derived/living_population_2025q3_sex_component.csv",
                "data/derived/living_population_2025q3_monthly_trend.csv",
            ],
            "analysis": "2025년 7-9월 월별 생활인구를 주민등록인구, 체류인구, 외국인으로 나누어 평균을 계산하고, 생활인구가 주민등록인구의 몇 배인지 산출했다.",
            "interpretation": "양양·고성·가평처럼 체류와 관광이 강한 지역은 주민등록인구만으로는 실제 생활 수요를 크게 과소평가한다. 다만 생활인구는 정착 인구가 아니라 방문과 체류의 규모이므로 출산 기반과 동일시해서는 안 된다.",
        },
        {
            "question": "생활인구는 어떤 연령과 성별로 구성되어 있으며, 월별로 어떻게 달라지는가?",
            "data": "행정안전부·통계청 2025년 3분기 인구감소지역 생활인구 산정 결과",
            "files": [
                "data/derived/living_population_2025q3_age_component.csv",
                "data/derived/living_population_2025q3_sex_component.csv",
                "data/derived/living_population_2025q3_monthly_trend.csv",
            ],
            "analysis": "주민등록인구, 체류인구, 외국인, 생활인구 전체를 구성별로 나누어 연령대 비중과 성별 비중을 계산하고, 2025년 7-9월 월별 총량 변화를 비교했다.",
            "interpretation": "체류인구의 연령·성별 구성이 정주인구와 다르면 생활인구는 단순한 규모 지표를 넘어 지역이 어떤 생활 기능을 갖는지 보여준다. 다만 3개월 자료는 장기 추세가 아니라 계절적 변화의 단서로 읽어야 한다.",
        },
        {
            "question": "사람들은 어느 시군구로 가장 많이 들어오고 있는가?",
            "data": "통계청 통계데이터센터 통신 모바일 인구이동량 통계 시군구 관내외 유입 자료(~2026.04.26)",
            "files": [
                "data/source/mobile_inflow_sigungu_20260426.xlsx",
                "data/derived/mobile_outside_migration_by_sex.csv",
                "data/derived/mobile_inflow_sigungu_2025_summary.csv",
            ],
            "analysis": "2025년 52개 주차의 주차별 일평균 유입 이동건수를 시군구별로 평균하고, 관내 이동과 관외 유입을 구분했다.",
            "interpretation": "강남·송파·서초·화성처럼 일자리와 생활서비스가 결합된 지역은 등록인구보다 훨씬 큰 이동 수요를 가진다. 지방 인구정책은 '몇 명이 사는가'와 함께 '누가 언제 들어와 무엇을 쓰는가'를 함께 보아야 한다.",
        },
    ],
    "section-3-0-sido-net-migration.html": [
        {
            "question": "어느 광역시도의 인구 순이동이 가장 큰가?",
            "data": "KOSIS DT_1B26001_A03 시군구/연령(5세)별 이동자수, 2000-2024년 광역시도 순이동",
            "files": [
                "data/domestic_migration_age_DT_1B26001_A03.csv",
                "data/derived/sido_net_migration_total.csv",
                "data/derived/sido_net_migration_age_by_year.csv",
                "data/derived/sido_net_migration_age_contribution.csv",
                "data/derived/sido_net_migration_age_model_summary.csv",
            ],
            "analysis": "광역시도별 총 순이동을 연도별 패널로 그리고, 최근 10년 평균 순이동을 연령대별 순이동의 합으로 분해한다.",
            "interpretation": "경기도는 가족 형성·주거 이동 연령층을 중심으로 순유입이 크고, 서울은 35-64세 유출이 커서 청년 유출만으로 설명되지 않는다.",
        }
    ],
    "section-3-1-regional-gap.html": [
        {
            "question": "어느 시군구가 먼저 초고령 구조에 들어갔는가?",
            "data": "KOSIS DT_1B04006 시군구별 1세별 주민등록인구, 2024년 고령화율",
            "files": ["data/derived/sigungu_aging_top.csv", "data/sigungu_aging_2024.csv", "map_data.js"],
            "analysis": "상위 시군구 막대그래프와 GIS 지도를 결합해 공간적 군집을 확인한다.",
            "interpretation": "고령화는 전국 평균보다 군 지역과 비수도권 생활권에서 먼저 정책 한계로 드러난다.",
        },
        {
            "question": "청년층 기반은 어디에서 약해지는가?",
            "data": "e-나라지표 청년 생산가능인구, 시군구 고령화율, 향후 국내이동 자료",
            "files": ["data/derived/youth_population_enara.csv", "data/sigungu_aging_2024.csv"],
            "analysis": "청년 생산가능인구 감소와 지역 고령화율을 연결하고, 후속으로 전입·전출 순이동을 붙인다.",
            "interpretation": "지역 인구감소는 출생 감소보다 청년 이동에서 먼저 관찰될 수 있다.",
        },
    ],
    "section-3-2-foreign-multicultural.html": [
        {
            "question": "외국인 유입은 노동, 유학, 결혼 중 무엇으로 구성되는가?",
            "data": "법무부/KOSIS 체류외국인 체류자격별 자료, 등록외국인 시군구·체류자격 자료",
            "files": ["data/foreign_residents_DT_1B040A5A.csv", "data/registered_foreigners_DT_1B040A11.csv"],
            "analysis": "체류자격별 규모와 지역 분포를 분해해 노동형, 유학형, 결혼·정착형 유입을 구분한다.",
            "interpretation": "외국인 인구는 단일 집단이 아니라 지역 노동시장과 가족 형성에 서로 다른 방식으로 작동한다.",
        },
        {
            "question": "다문화 출생 비중은 출생 구조를 얼마나 바꾸는가?",
            "data": "KOSIS 지역별 다문화 출생, 국제결혼 관련 자료",
            "files": ["data/derived/multicultural_birth_rate.csv", "data/international_marriage_DT_1BB0006.csv"],
            "analysis": "전체 출생아 수, 다문화 출생아 수, 다문화 출생 비중을 같은 표로 비교한다.",
            "interpretation": "출생아 수가 줄수록 다문화 출생은 지역 교육과 돌봄 체계에서 더 중요한 비중을 갖는다.",
        },
    ],
    "section-4-1-family-formation.html": [
        {
            "question": "한국에서 출생은 혼인과 얼마나 강하게 묶여 있는가?",
            "data": "KOSIS 인구동태의 출생, 혼인, 이혼, 법적혼인상태별 출생 자료",
            "files": ["data/derived/fertility_comparison.csv", "data/international_marriage_DT_1BB0006.csv"],
            "analysis": "조혼인율, 조출생률, 조이혼율을 시도 패널로 만들고 산점도·상관계수를 계산한다.",
            "interpretation": "혼인과 출생의 상관은 주거, 소득, 돌봄 조건을 통과해 나타나는 결과로 해석해야 한다.",
        },
        {
            "question": "혼인 밖 출생이 낮은 구조는 출산율 하락을 어떻게 증폭하는가?",
            "data": "법적혼인상태별 출생, 전체 출생아 수, 혼인 건수",
            "files": ["data/international_marriage_DT_1BB0006.csv"],
            "analysis": "혼외 출생 비중과 혼인 감소 시점을 같이 놓고 출생 감소의 제도적 경로를 확인한다.",
            "interpretation": "혼인 감소가 곧바로 출생 감소로 이어지는 한국적 구조를 설명한다.",
        },
    ],
    "section-4-1-marriage-culture.html": [
        {
            "question": "결혼과 출산은 왜 문화적 현상인가?",
            "data": "국가데이터처·통계청 2010년·2024년 사회조사, 2023년 청년 의식변화 기획보도, 저출산고령사회위원회 25-29세 여성 인식조사, KOSIS 합계출산율, 한국행정연구원 사회통합실태조사",
            "files": [
                "data/derived/marriage_attitude_unmarried_gender.csv",
                "data/derived/family_norms_culture_shift.csv",
                "data/derived/marriage_attitude_youth_profile_2022.csv",
                "data/derived/young_women_25_29_recent_attitudes.csv",
                "data/derived/tfr_gender_conflict_timeline.csv",
            ],
            "analysis": "미혼 남녀의 결혼 긍정 인식, 청년 성별·연령대별 결혼 긍정 인식, 25-29세 여성의 결혼 의향·자녀 필요성, 합계출산율 급락과 남녀 갈등 인식의 시간적 겹침을 비교한다.",
            "interpretation": "결혼 규범은 약해졌지만 출산과 양육 제도는 여전히 혼인을 중심으로 작동한다. 2010년대 후반의 남녀 갈등과 사회적 비관은 이 간극을 더 크게 만드는 문화적 조건으로 해석하되, 인과효과로 단정하지 않는다.",
        }
    ],
    "section-4-1-divorce-fear-marriage.html": [
        {
            "question": "30대와 40대의 이혼율은 증가하고 있는가?",
            "data": "KOSIS DT_1B85009 시도/성/연령별 이혼율, 전국 계, 2000-2024년",
            "files": ["data/divorce_rate_by_age_DT_1B85009.csv", "data/derived/divorce_rate_30s_40s_trend.csv"],
            "analysis": "남편·아내별로 30-34세와 35-39세를 30대, 40-44세와 45-49세를 40대로 묶어 해당연령 천명당 이혼율의 추세를 비교한다.",
            "interpretation": "최근의 가족 불안은 30대 이혼율 급증이라기보다 혼인 연령 상승과 40대 이후 이혼위험의 상대적 두꺼워짐으로 읽는 것이 더 적절하다.",
        },
        {
            "question": "이혼에 대한 사회적 수용도는 어느 정도인가?",
            "data": "국가데이터처·통계청 2024년 사회조사 결과 보도자료와 KOSIS DT_1SSFA070R 이혼에 대한 견해",
            "files": ["data/derived/divorce_acceptance_trend.csv", "data/derived/divorce_acceptance_profile_2024.csv"],
            "analysis": "‘이유가 있으면 이혼을 하는 것이 좋다’ 응답 추세와 2024년 집단별 부정·중립·긍정 응답을 비교한다.",
            "interpretation": "이혼 수용도는 높아졌지만, 결혼하지 않는 이유의 주류는 여전히 결혼자금, 양육 부담, 고용 불안이다. 이혼 두려움은 핵심 원인이라기보다 결혼의 장기 위험을 크게 느끼게 하는 보조 요인으로 해석해야 한다.",
        },
    ],
    "section-4-2-men-care-parental-leave.html": [
        {
            "question": "출산휴가자는 줄고 있는가, 늘고 있는가?",
            "data": "e-나라지표 150401 출산전후휴가 및 육아휴직급여 현황",
            "files": ["data/derived/maternity_leave_support.csv", "data/enara_150401_raw.html"],
            "analysis": "출산전후휴가급여 초회수급자 수, 총 지원금액, 1인당 지원금액을 연도별로 계산한다.",
            "interpretation": "출산아 수가 줄어도 고용보험 안에서 보호되는 출산휴가 급여 지출은 제도 단가 상승과 대상 확대에 따라 달라질 수 있다.",
        },
        {
            "question": "출산전후휴가급여와 육아휴직급여의 재원을 고용보험이 계속 감당할 수 있는가?",
            "data": "e-나라지표 150401 출산전후휴가 및 육아휴직급여 현황과 고용노동부 일가정양립 정책자료",
            "files": ["data/derived/maternity_parental_leave_financing_pressure.csv", "data/enara_150401_raw.html"],
            "analysis": "출산전후휴가급여와 육아휴직급여 지원금액을 조원 단위로 환산하고 합계 및 항목별 지출 증가를 비교한다.",
            "interpretation": "출산·육아기 소득 중단 보장은 고용보험의 역할과 맞닿아 있지만, 저출산 대응이라는 사회 전체 목적은 일반재정 분담과 사각지대 보완을 함께 요구한다.",
        },
        {
            "question": "육아휴직의 추세는 남성과 여성에서 어떻게 다르게 움직이는가?",
            "data": "e-나라지표 150401의 육아휴직급여 초회수급자 성별 자료",
            "files": ["data/derived/parental_leave_gender_users.csv", "data/enara_150401_raw.html"],
            "analysis": "전체, 여성근로자, 남성근로자의 수급자 수와 남성 비중을 계산한다.",
            "interpretation": "남성 수급자 증가는 돌봄 태도의 변화를 보여주지만, 여성 수급자가 여전히 더 많은 구조는 돌봄 책임의 불균형이 남아 있음을 뜻한다.",
        },
        {
            "question": "1인당 육아휴직 지원금액은 얼마나 증가했는가?",
            "data": "e-나라지표 150401의 육아휴직급여 지원금액과 수급자 수",
            "files": ["data/derived/parental_leave_per_user_support.csv", "data/enara_150401_raw.html"],
            "analysis": "총 지원금액을 수급자 수로 나누어 전체 1인당 지원금액을 산출하고, 성별 1인당 지원금액도 같은 방식으로 계산한다.",
            "interpretation": "급여 수준 상승은 육아휴직 이용의 문턱을 낮추지만, 남성 이용 확대와 결합할수록 재정 규모가 빠르게 커진다.",
        },
        {
            "question": "남자와 여자의 1인당 육아휴직 지원금액은 왜 다른가?",
            "data": "e-나라지표 150401의 성별 육아휴직급여 수급자 수와 지원금액",
            "files": ["data/derived/parental_leave_per_user_support.csv"],
            "analysis": "남성근로자와 여성근로자의 1인당 지원금액 격차와 변화율을 비교한다.",
            "interpretation": "성별 1인당 금액 격차는 급여 산식뿐 아니라 휴직 기간, 임금 수준, 이용 시점, 기업문화가 결합된 결과로 해석해야 한다.",
        },
        {
            "question": "남성은 실제로 아이 돌보는 시간을 늘리고 있는가?",
            "data": "통계청 2024년 생활시간조사 결과의 미취학 자녀 가구 시간사용",
            "files": ["data/derived/preschool_childcare_time_by_parent.csv"],
            "analysis": "2019년과 2024년의 남편·아내 돌보기 시간을 분 단위로 환산하고, 부모 합산 돌보기 시간 중 남편 비중을 계산한다.",
            "interpretation": "남편의 돌보기 시간은 늘었지만 아내의 시간이 여전히 훨씬 길다. 제도 이용 확대가 일상적 돌봄 평등으로 이어지는지는 별도로 점검해야 한다.",
        },
        {
            "question": "맞벌이 가구에서도 가사노동은 평등해지고 있는가?",
            "data": "통계청 2024년 생활시간조사 결과의 18세 미만 자녀가 있는 맞벌이 가구 시간사용",
            "files": ["data/derived/dual_earner_child_housework_time.csv"],
            "analysis": "2019년과 2024년의 남편·아내 가사노동 시간을 비교하고, 부부 합산 가사노동 시간 중 남편 비중을 계산한다.",
            "interpretation": "맞벌이 가구에서 남편의 가사노동 비중은 상승했지만 2024년에도 30%에 미치지 못한다. 저출산 정책은 휴직급여뿐 아니라 일상 시간의 재배분을 겨냥해야 한다.",
        },
    ],
    "section-4-3-care-work-balance.html": [
        {
            "question": "부모가 실제 생활권에서 필요한 시간에 믿고 맡길 수 있는가?",
            "data": "KOSIS DT_15407_NN009 특수보육어린이집 현황, 중앙육아종합지원센터 시간제보육 및 어린이집 이용시간 안내",
            "files": ["data/derived/childcare_time_flexible_facilities.csv", "data/special_childcare_DT_15407_NN009.csv"],
            "analysis": "야간 연장, 24시간, 휴일 보육 어린이집 수와 전체 어린이집 대비 비중, 해당 보육 아동현원을 계산한다.",
            "interpretation": "전국 어린이집 총량보다 부모의 출퇴근·야간·휴일 생활시간과 맞는 시간 접근성이 실제 돌봄 가능성을 좌우한다.",
        },
        {
            "question": "육아휴직과 일가정양립 제도는 실제로 누가 이용하는가?",
            "data": "고용보험 육아휴직 통계, 성별·산업별 육아휴직 이용 자료, KOSIS 보육 관련 통계",
            "files": ["data/openfiscal_population_budget.csv"],
            "analysis": "육아휴직 이용자 수, 남성 비중, 산업별 이용 격차를 계산하고 보육 인프라 변화와 함께 읽는다.",
            "interpretation": "제도가 존재해도 이용 가능성이 성별과 일자리 안정성에 따라 다르면 출산 결정의 불확실성은 줄지 않는다.",
        },
        {
            "question": "돌봄 부담은 가족 형성 조건과 어떻게 연결되는가?",
            "data": "보육통계, 육아휴직 자료, 열린재정 보육·가족 예산",
            "files": ["data/openfiscal_population_budget.csv"],
            "analysis": "보육 공급, 휴직 이용, 재정 지출을 묶어 돌봄의 시간·공간·비용 조건을 비교한다.",
            "interpretation": "저출산 대책은 현금지원보다 돌봄 인프라와 노동시간 제도의 결합으로 평가해야 한다.",
        },
    ],
    "section-4-4-childcare-shortage.html": [
        {
            "question": "어린이집 유형별 개소 수는 어떻게 바뀌었는가?",
            "data": "KOSIS DT_15407_NN001 어린이집 설치·운영 현황",
            "files": ["data/derived/childcare_supply_by_type.csv", "data/parental_leave_DT_15407_NN001.csv"],
            "analysis": "국공립, 사회복지법인, 법인·단체 등, 민간, 가정, 협동, 직장 어린이집의 연도별 개소 수와 정점 이후 감소폭을 계산한다.",
            "interpretation": "전체 시설 수보다 중요한 것은 민간·가정 시설 축소와 공공·직장 시설 확대가 동시에 진행되는 공급 구조의 전환이다.",
        },
        {
            "question": "어린이집 이용자수, 곧 보육아동수는 증가하고 있는가?",
            "data": "KOSIS DT_15407_NN002 어린이집 보육아동 현황",
            "files": ["data/derived/childcare_users_by_type.csv", "data/childcare_children_DT_15407_NN002.csv"],
            "analysis": "유형별 보육아동수의 정점연도, 최근 연도 수준, 감소폭을 계산하고 시설 수 변화와 비교한다.",
            "interpretation": "보육아동수는 2014년 정점 이후 뚜렷하게 감소한다. 이는 어린이집 부족이 전국 총량 부족이라기보다 생활권별 접근성 문제로 나타날 가능성을 뜻한다.",
        },
        {
            "question": "시설이 줄어드는 것이 출산 결정에 어떤 정책 문제를 만드는가?",
            "data": "KOSIS 어린이집 설치·운영 현황과 보육아동 현황의 연도·유형 결합 자료",
            "files": ["data/derived/childcare_supply_users_by_type.csv", "data/derived/childcare_capacity_pressure.csv"],
            "analysis": "시설 수, 이용 아동 수, 시설당 아동수, 유형별 비중을 결합해 보육 인프라 축소가 총량 조정인지 접근성 약화인지 구분한다.",
            "interpretation": "출생 감소가 민간·가정 어린이집 폐원으로 이어지면, 다음 세대 부모에게는 가까운 돌봄 선택지의 축소로 돌아온다. 보육정책은 정원 관리가 아니라 생활권 접근성 관리가 되어야 한다.",
        },
    ],
    "section-4-5-household-housing.html": [
        {
            "question": "인구가 줄어도 주택 수요는 왜 바로 줄지 않는가?",
            "data": "KOSIS 빈집비율, 장래가구추계, 1인가구·고령가구 자료",
            "files": ["data/derived/vacant_housing_rate.csv", "data/elderly_economic_activity.csv"],
            "analysis": "빈집비율과 빈집 수, 가구수 전망, 가구주 연령구조를 연결한다.",
            "interpretation": "총인구 감소와 가구·주거 수요는 시간차를 두고 어긋난다.",
        },
        {
            "question": "빈집은 어느 지역에서 생활권 약화의 신호가 되는가?",
            "data": "시도·시군구 빈집비율, 시군구 고령화율",
            "files": ["data/sigungu_aging_2024.csv", "data/elderly_economic_activity.csv"],
            "analysis": "빈집률과 고령화율을 지도와 산점도로 결합한다.",
            "interpretation": "빈집은 주택 문제가 아니라 학교, 상권, 의료, 교통 접근성이 함께 약해지는 생활권 지표다.",
        },
    ],
    "section-4-5-households.html": [
        {
            "question": "가구 수는 왜 인구와 다르게 움직이는가?",
            "data": "KOSIS INH_1JC1501 가구수(시도/시/군/구), DT_1B040A3 시군구 주민등록인구",
            "files": ["data/derived/household_population_gap_national.csv", "data/derived/household_population_gap_all_regions.csv"],
            "analysis": "2015년을 100으로 두고 전국 가구 수 지수, 인구 지수, 평균 가구원 수를 계산한다.",
            "interpretation": "인구가 정체되어도 1인가구, 고령가구, 비혼·만혼, 가족 분화가 늘면 가구 수는 계속 증가할 수 있다.",
        },
        {
            "question": "가구 수와 인구의 괴리는 수도권에서만 나타나는가?",
            "data": "KOSIS INH_1JC1501 시도별 가구수와 시군구 주민등록인구의 시도 합산값",
            "files": ["data/derived/household_population_gap_regions.csv"],
            "analysis": "시도별 2015-2024년 가구 수 증가율과 인구 증가율을 비교하고, 수도권과 비수도권을 구분한다.",
            "interpretation": "가구 수 증가가 인구 증가를 앞서는 현상은 수도권만의 현상이 아니라 대부분 지역에서 관찰되는 생활단위 변화다.",
        },
        {
            "question": "가구주의 고령화와 청년 1인가구 증가는 동시에 일어나는가?",
            "data": "KOSIS DT_1JC1511 가구주의 연령 및 가구원수별 가구(일반가구) - 시군구, 전국",
            "files": ["data/derived/household_head_age_shift.csv", "data/household_head_age_size_DT_1JC1511.csv"],
            "analysis": "가구주 20-34세 1인가구와 65세 이상 가구주 가구·1인가구를 집계하고 2015년 대비 증가율과 일반가구 대비 비중을 계산한다.",
            "interpretation": "청년 1인가구 증가는 가족 형성의 지연을, 고령 1인가구 증가는 생애 후반 가족 분화와 돌봄 수요 증가를 보여준다.",
        },
    ],
    "section-4-6-housing-demand.html": [
        {
            "question": "주거 수요는 왜 인구보다 늦게 줄어드는가?",
            "data": "KOSIS DT_1BZ0503 가구주의 연령/가구원수별 추계가구-전국",
            "files": ["data/derived/future_households_policy.csv", "data/future_households_DT_1BZ0503.csv"],
            "analysis": "총가구, 1인가구, 2인가구, 4인가구의 장기 추세를 비교한다.",
            "interpretation": "주거 수요는 사람 수보다 가구 형태에 더 직접적으로 반응한다. 작은 가구가 늘면 인구 감소가 곧 주택 수요 감소로 이어지지 않는다.",
        },
    ],
    "section-4-7-vacant-housing.html": [
        {
            "question": "빈집은 생활권 약화의 신호인가?",
            "data": "KOSIS DT_1YL202005 미거주주택(빈집)비율, 국가데이터처 인구주택총조사, 관계부처합동 2022년 빈집실태조사",
            "files": ["data/derived/vacant_housing_policy.csv", "data/derived/vacant_housing_rate.csv", "data/derived/vacant_housing_definition_gap_2022.csv", "data/derived/molit_vacant_housing_2022.csv", "data/elderly_economic_activity.csv"],
            "analysis": "전국 빈집률, 빈집 수, 전체 주택 수의 추세를 비교하고, 2022년 KOSIS 미거주주택과 국토교통부 등 관계부처의 장기 빈집 수를 별도로 비교한다.",
            "interpretation": "빈집은 단순한 주택 잔여물이 아니라 인구, 가구, 생활서비스가 어긋나는 지역에서 나타나는 공간적 신호다. KOSIS 통계는 넓은 공실 저량을 보는 탐색 지표이고, 국토부 등 빈집실태조사는 실제 정비·활용·철거 대상에 가까운 집행 지표다.",
        },
    ],
    "section-5-1-labor-aging.html": [
        {
            "question": "고령층에서 취업자는 얼마나 빠르게 증가하고 있을까?",
            "data": "KOSIS DT_1DE8031S 경제활동인구조사 고령층 부가조사, 2010-2025년 매년 5월",
            "files": ["data/derived/elderly_labor_dt_1de8031s_trends.csv", "data/derived/elderly_labor_dt_1de8031s_summary.csv", "data/elderly_labor_DT_1DE8031S.csv"],
            "analysis": "전국은 55~79세 전체와 55~64세, 65~79세의 취업자 추세를 분리해 보고, 지역은 KOSIS 시도별 표에서 60세 이상 취업자에 대해 year → 취업자 회귀계수를 계산한다.",
            "interpretation": "전국 취업자 증가는 은퇴 지연과 노후소득 필요가 겹친 결과다. 지역 회귀계수는 이 변화가 수도권처럼 고령 인구 자체가 빠르게 늘어난 곳에서 큰지, 농어촌처럼 이미 고령화된 곳에서 완만한지 비교하게 해 준다.",
        },
        {
            "question": "고령층에서 고용률은 얼마나 빠르게 증가하고 있을까?",
            "data": "KOSIS DT_1DE8031S 고용률과 DT_1DA7015S 시도별 60세 이상 고용률",
            "files": ["data/derived/elderly_labor_dt_1de8031s_trends.csv", "data/derived/elderly_regional_labor_60plus_slopes.csv", "data/derived/elderly_regional_labor_60plus_trends.csv"],
            "analysis": "전국 고용률 추세를 먼저 읽고, 시도별 60세 이상 고용률에 대해 연도 회귀계수를 계산해 퍼센트포인트/년 단위의 변화 속도를 비교한다.",
            "interpretation": "고용률이 빠르게 오른 지역은 단순히 노인이 많아진 곳이 아니라 고령층이 실제 노동시장에 더 많이 남거나 들어온 곳이다. 이 값은 고령 친화 일자리, 자영업 구조, 농어업 비중, 지역 노후소득 조건을 함께 묻게 만든다.",
        },
        {
            "question": "고령층에서 실업자는 얼마나 빠르게 증가하고 있을까?",
            "data": "KOSIS DT_1DE8031S 실업자와 DT_1DA7095S 시도별 60세 이상 실업자",
            "files": ["data/derived/elderly_labor_dt_1de8031s_trends.csv", "data/derived/elderly_regional_labor_60plus_slopes.csv", "data/regional_elderly_unemployed_DT_1DA7095S.csv"],
            "analysis": "전국 55~79세 실업자 추세와 시도별 60세 이상 실업자의 연도 회귀계수를 함께 본다. 실업자 표는 60세 이상 범주가 공통으로 제공되어 이 범주를 사용한다.",
            "interpretation": "실업자 증가는 취업자 증가보다 규모가 작지만, 고령층이 구직자로 노동시장 안에 남는 정도를 보여준다. 회귀계수가 큰 지역은 고령층 일자리 수요가 실제 구직 압력으로 드러나는 곳이다.",
        },
        {
            "question": "고령층에서 비경제활동인구는 얼마나 빠르게 증가하고 있을까?",
            "data": "KOSIS DT_1DE8031S 비경제활동인구와 DT_1DA7015S 시도별 60세 이상 비경제활동인구",
            "files": ["data/derived/elderly_labor_dt_1de8031s_trends.csv", "data/derived/elderly_regional_labor_60plus_slopes.csv", "data/regional_elderly_labor_DT_1DA7015S.csv"],
            "analysis": "전국과 지역 모두 비경제활동인구를 취업자·실업자와 별도로 분리해 추세를 본다. 시도별 회귀계수는 노동시장 밖에 있는 고령층 규모가 매년 얼마나 늘었는지 보여준다.",
            "interpretation": "비경제활동인구 증가는 노동시장으로 끌어낼 ‘잠재 인력’만을 뜻하지 않는다. 건강, 돌봄, 은퇴, 구직 포기, 소득보장 조건이 섞여 있기 때문에 고용정책과 복지정책을 함께 읽어야 한다.",
        },
        {
            "question": "고령층은 언제 주된 일자리에서 나오고, 왜 다시 일하려 하는가?",
            "data": "KOSIS DT_1DE8035S, DT_1DE8036S, DT_1DE8037S, DT_1DE8038S, DT_1DE8042S, DT_1DE8044S, DT_1DE8057S 고령층 부가조사",
            "files": ["data/derived/elderly_activity_life_course_indicators.csv", "data/derived/elderly_activity_exit_reasons_2025.csv", "data/derived/elderly_activity_future_work_reasons_2025.csv"],
            "analysis": "평균 근속기간, 평균 이직연령, 지난 1년간 구직·취업 경험, 장래 근로 희망률, 희망 근로연령을 연도별로 연결하고 2025년의 이직 사유와 근로 희망 사유를 분해한다.",
            "interpretation": "고령층 경제활동은 은퇴 이후의 단순한 재취업 문제가 아니다. 주된 일자리에서 이탈한 뒤 생활비, 건강, 돌봄, 일의 보람이 뒤섞여 다시 노동시장과 연결되는 생애경로 문제다.",
        },
        {
            "question": "고령층은 어떤 조건의 일자리를 원하는가?",
            "data": "KOSIS DT_1DE8046S, DT_1DE8048S, DT_1DE8050S 고령층 부가조사",
            "files": ["data/derived/elderly_activity_job_preferences_2025.csv"],
            "analysis": "장래 근로 희망자를 분모로 일자리 선택기준, 희망 일자리 형태, 희망 임금수준을 성별과 전체 기준으로 비교한다.",
            "interpretation": "고령층이 원하는 일자리는 단순히 임금이 높은 일만이 아니다. 일의 양과 시간대, 계속 일할 수 있는 가능성, 출퇴근 편의가 핵심 조건으로 떠오른다.",
        },
        {
            "question": "고령층 취업자는 어느 산업과 직업에 집중되어 있는가?",
            "data": "KOSIS DT_1DE8061_11 연령/산업별 취업분포, DT_1DE8063_8 연령/직업별 취업분포",
            "files": ["data/derived/elderly_employment_structure_2025.csv"],
            "analysis": "2025년 55~79세 취업자가 산업·직업별로 어디에 분포하는지 계산하고, 전체 고령층 취업자 중 해당 범주의 비중을 비교한다.",
            "interpretation": "고령층 노동은 특정 산업의 주변부에만 존재하지 않는다. 서비스·판매, 단순노무, 기능·기계조작, 농림어업, 공공·개인서비스가 고령층 일자리의 실제 지형을 만든다.",
        },
    ],
    "section-5-2-aging-index.html": [
        {
            "question": "노령화지수는 무엇을 측정하는가?",
            "data": "KOSIS DT_1BPB002 주요 인구지표의 0-14세 구성비, 65세 이상 구성비, 노령화지수",
            "files": ["data/derived/aging_index_growth.csv", "data/derived/national_population_pressure.csv", "data/population_projection_indicators.csv"],
            "analysis": "노령화지수 = 65세 이상 인구 / 0-14세 인구 × 100으로 해석하고, 유소년 비중과 고령층 비중을 같은 그림에 배치한다.",
            "interpretation": "노령화지수는 고령화와 저출산이 한꺼번에 사회의 세대 균형을 어떻게 바꾸는지 보여준다.",
        },
        {
            "question": "노령화지수는 얼마나 빠르게 증가했는가?",
            "data": "KOSIS 장래인구추계 중위추계, 2000-2052년",
            "files": ["data/derived/aging_index_growth.csv"],
            "analysis": "2000년, 2025년, 2052년 값을 비교하고 100, 200, 300, 500을 넘는 시점을 확인한다.",
            "interpretation": "한국은 2017년에 노령화지수 100을 넘었고, 2026년에 200, 2030년에 300, 2050년에 500을 넘는 구조로 이동한다.",
        },
    ],
    "section-5-3-lifecycle-fiscal.html": [
        {
            "question": "고령화는 재정의 어느 항목을 압박하는가?",
            "data": "열린재정 국가채무·재정지표, 향후 보건·연금·돌봄 예산",
            "files": ["data/derived/openfiscal_debt_context.csv", "data/openfiscal_population_budget.csv"],
            "analysis": "국가채무 흐름을 배경선으로 두고 인구 관련 세출 기능을 별도 묶음으로 추적한다.",
            "interpretation": "재정 문제는 단순 부채 규모가 아니라 세대별 소비와 부담의 배분 문제다.",
        },
        {
            "question": "생애주기에서 적자와 흑자는 어느 나이에 발생하는가?",
            "data": "KOSIS 국민이전계정, 연령별 노동소득·소비·공공이전 자료",
            "files": ["data/openfiscal_population_budget.csv"],
            "analysis": "연령별 노동소득과 소비 차이를 계산해 생애주기 적자 곡선을 만든다.",
            "interpretation": "저출산·고령화는 아이와 노인이 많고 적다는 문제가 아니라 세대 간 이전 구조의 재편이다.",
        },
    ],
    "section-5-3-health-spending-aging.html": [
        {
            "question": "연령별 1인 공공보건소비는 어느 나이부터 빠르게 증가하는가?",
            "data": "KOSIS DT_1NTA2003 생애주기적자계정(1인규모)의 공공보건소비",
            "files": ["data/national_transfer_accounts_DT_1NTA2003.csv", "data/derived/nta_public_health_age_profile.csv"],
            "analysis": "2010, 2015, 2020, 2022년을 선택해 X축을 각세 연령, Y축을 1인 공공보건소비로 놓고 연령 프로필을 비교한다.",
            "interpretation": "의료비 압력은 고령층 전체에서 균일하게 증가하지 않는다. 후기고령층으로 갈수록 1인당 지출이 가파르게 커지므로 고령화 재정은 연령구성의 세부 변화까지 보아야 한다.",
        },
        {
            "question": "같은 연령대의 공공보건소비는 2010년 이후 얼마나 늘었는가?",
            "data": "DT_1NTA2003 공공보건소비를 0-14세, 15-44세, 45-64세, 65-74세, 75-84세, 85세 이상으로 재분류한다.",
            "files": ["data/derived/nta_public_health_age_group_trend.csv"],
            "analysis": "각 연령대 내부 각세별 1인 공공보건소비를 단순 평균하고 연도별 추세를 비교한다.",
            "interpretation": "총의료비 증가는 고령층 인구 증가와 1인당 비용 상승이 동시에 작동한 결과다. 따라서 해법은 단순 삭감이 아니라 예방, 만성질환 관리, 지역 의료 접근성, 장기요양과 의료의 연결을 포함해야 한다.",
        },
    ],
    "section-5-4-aging-budget.html": [
        {
            "question": "고령화 관련 세부사업 수는 늘었는가?",
            "data": "열린재정 VW_OPFI940 세부사업 예산편성현황(총지출), 2007-2026년",
            "files": ["data/derived/openfiscal_aging_budget_trends.csv", "data/openfiscal_VW_OPFI940_aging_budget_matches.csv"],
            "analysis": "세부사업명에 노인·고령·기초연금·기초노령연금·장기요양·치매 등 키워드가 포함된 사업을 추출하고, 연도별 고유 세부사업명 수와 세부사업-소관-회계 단위 수를 함께 계산한다.",
            "interpretation": "사업 수 증가는 정책 영역의 확산을 보여주지만, 사업 수가 줄어도 큰 급여성 사업이 커지면 재정 압력은 더 강해질 수 있다.",
        },
        {
            "question": "고령화 관련 예산 금액은 얼마나 증가했는가?",
            "data": "열린재정 TotalExpenditure5 API, 금액 변수 Y_YY_DFN_MEDI_KCUR_AMT",
            "files": ["data/derived/openfiscal_aging_budget_trends.csv", "data/derived/openfiscal_aging_budget_category_trends.csv"],
            "analysis": "예산액을 천원에서 조원으로 환산하고 기초연금, 노인일자리, 장기요양·치매, 노인돌봄, 기타 노인·고령화 항목으로 나누어 추세를 계산한다.",
            "interpretation": "증가의 대부분은 기초연금에서 발생한다. 장기요양·치매와 노인일자리는 고령사회 서비스와 노동시장 대응의 확대를 보여주지만, 전체 재정 규모에서는 현금급여가 압도적이다.",
        },
        {
            "question": "최근 연도 예산은 어떤 세부사업에 집중되는가?",
            "data": "최근 제공 연도 열린재정 세부사업 예산",
            "files": ["data/derived/openfiscal_aging_budget_top_programs_latest.csv"],
            "analysis": "최근 연도 세부사업을 예산액 기준으로 정렬해 상위 사업을 확인한다.",
            "interpretation": "고령화 예산은 넓게 흩어진 작은 사업들의 합이 아니라 기초연금지급, 장기요양보험, 노인일자리 같은 몇 개의 큰 제도에 의해 방향이 결정된다.",
        },
    ],
    "section-5-5-elderly-pension.html": [
        {
            "question": "고령층의 월평균 연금수령액은 얼마나 증가했는가?",
            "data": "KOSIS DT_1DE8051S 성별 연금수령여부 및 월평균수령액, 2008-2025년 매년 5월",
            "files": ["data/derived/elderly_pension_dt_1de8051s_trends.csv", "data/derived/elderly_pension_dt_1de8051s_summary.csv", "data/elderly_pension_DT_1DE8051S.csv"],
            "analysis": "성별 평균수령액을 시계열로 만들고 2008년과 2025년의 변화액과 변화율을 계산한다.",
            "interpretation": "평균수령액 증가는 연금제도의 성숙을 보여주지만, 평균 수준만으로 노후소득 안정이 충분하다고 판단할 수는 없다.",
        },
        {
            "question": "연금을 받는 고령층의 비율은 얼마나 늘었는가?",
            "data": "KOSIS DT_1DE8051S의 55~79세 인구와 연금수령자 항목",
            "files": ["data/derived/elderly_pension_dt_1de8051s_trends.csv"],
            "analysis": "연금수령자/55~79세 인구×100으로 연금수령률을 계산하고 평균수령액과 같은 그림에 배치한다.",
            "interpretation": "수령률 상승은 제도 포괄성이 넓어진다는 뜻이지만, 받는 금액의 충분성과 성별 격차를 함께 보아야 한다.",
        },
    ],
    "section-5-6-elderly-pension-distribution.html": [
        {
            "question": "연금수령액 구간은 낮은 금액에서 높은 금액으로 이동했는가?",
            "data": "KOSIS DT_1DE8051S의 월평균 10만원 미만, 10~25만원, 25~50만원, 50~100만원, 100만원 이상 구간",
            "files": ["data/derived/elderly_pension_dt_1de8051s_distribution.csv"],
            "analysis": "각 구간의 수령자 수를 전체 연금수령자로 나누어 구간별 비중을 계산한다.",
            "interpretation": "낮은 금액 구간이 줄고 50만원 이상 구간이 늘어나는 것은 연금제도 성숙의 신호지만, 여전히 중간 이하 구간이 두터운 구조는 노후소득 보장의 한계를 보여준다.",
        },
    ],
}


def esc(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def manuscript_name(html_file: str) -> str:
    return f"{Path(html_file).stem}.md"


def chapter_manuscript_path(chapter: dict) -> Path:
    return CHAPTER_MANUSCRIPTS / manuscript_name(chapter["file"])


def section_manuscript_path(section: dict) -> Path:
    return SECTION_MANUSCRIPTS / manuscript_name(section["file"])


def chart_shortcode(chart_id: str, size: str = "") -> str:
    suffix = f"|{size}" if size else ""
    return f"{{{{chart:{chart_id}{suffix}}}}}"


def inline_markdown(text: str) -> str:
    escaped = escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def render_chart_panel(chart_id: str, rel: str = "..", size: str = "") -> str:
    if chart_id not in CHART_META:
        return f"""<section class="panel markdown-warning">
  <h2>알 수 없는 그림</h2>
  <p class="source-note">마크다운 원고의 차트 ID <code>{esc(chart_id)}</code>를 CHART_META에서 찾을 수 없다.</p>
</section>"""
    meta = CHART_META[chart_id]
    chart_class = "chart-box book-chart"
    panel_class = "panel markdown-chart-panel"
    if size == "small":
        chart_class += " small-book-chart"
        panel_class += " small-chart-panel"
    csv_href = f"{rel}/data/derived/{meta['csv']}"
    return f"""<section class="{panel_class}">
  <div class="chart-panel-header">
    <h2>{esc(meta["title"])}</h2>
    <a class="csv-button" href="{csv_href}" download>CSV 다운로드</a>
  </div>
  <div class="{chart_class}"><canvas data-book-chart="{esc(chart_id)}"></canvas></div>
  <div class="chart-actions source-actions">
    <span>출처: {esc(meta["source"])}</span>
  </div>
  <p class="source-note">{esc(meta["note"])}</p>
</section>"""


def render_markdown(markdown: str, rel: str = "..") -> str:
    """Render editable book manuscripts, including chart shortcodes."""
    blocks: list[str] = []
    lines = markdown.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == r"\[":
            math_lines = [line]
            i += 1
            while i < len(lines):
                math_lines.append(lines[i].strip())
                if lines[i].strip() == r"\]":
                    i += 1
                    break
                i += 1
            blocks.append(f'<div class="math-block">{" ".join(escape(part, quote=False) for part in math_lines)}</div>')
            continue
        pause_match = re.fullmatch(r":::\s*pause(?:\s+(.+))?", line)
        if pause_match:
            title = pause_match.group(1) or "쉬어가기"
            inner_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                inner_lines.append(lines[i])
                i += 1
            if i < len(lines) and lines[i].strip() == ":::":
                i += 1
            inner_html = render_markdown("\n".join(inner_lines), rel=rel)
            blocks.append(
                f"""<aside class="pause-box">
  <h2>{inline_markdown(title)}</h2>
  <div class="pause-box-body">
{inner_html}
  </div>
</aside>"""
            )
            continue
        chart_match = re.fullmatch(r"\{\{chart:([A-Za-z0-9_\-]+)(?:\|([A-Za-z0-9_\-]+))?\}\}", line)
        if chart_match:
            blocks.append(render_chart_panel(chart_match.group(1), rel=rel, size=chart_match.group(2) or ""))
            i += 1
            continue
        if re.fullmatch(r"\{\{aging_budget_program_table\}\}", line):
            blocks.append(aging_budget_program_table_html())
            i += 1
            continue
        image_match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", line)
        if image_match:
            alt, src = image_match.groups()
            blocks.append(
                f"""<figure class="markdown-figure">
  <img src="{esc(src)}" alt="{esc(alt)}">
  <figcaption>{inline_markdown(alt)}</figcaption>
</figure>"""
            )
            i += 1
            continue
        heading_match = re.match(r"^(#{2,4})\s+(.+)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            blocks.append(f"<h{level}>{inline_markdown(heading_match.group(2))}</h{level}>")
            i += 1
            continue
        if line.startswith("|") and "|" in line[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = [[cell.strip() for cell in row.strip("|").split("|")] for row in table_lines]
            if len(rows) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell or "---") for cell in rows[1]):
                header = "".join(f"<th>{inline_markdown(cell)}</th>" for cell in rows[0])
                body_rows = []
                for row in rows[2:]:
                    body_rows.append("<tr>" + "".join(f"<td>{inline_markdown(cell)}</td>" for cell in row) + "</tr>")
                blocks.append(
                    f"""<div class="data-table-wrap markdown-table-wrap">
  <table class="data-table markdown-table">
    <thead><tr>{header}</tr></thead>
    <tbody>{''.join(body_rows)}</tbody>
  </table>
</div>"""
                )
            continue
        if line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(f"<li>{inline_markdown(lines[i].strip()[2:].strip())}</li>")
                i += 1
            blocks.append(f"<ul>{''.join(items)}</ul>")
            continue
        paragraph_lines = [line]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if (
                not next_line
                or next_line.startswith("##")
                or next_line.startswith("- ")
                or next_line.startswith("|")
                or next_line.startswith("![")
                or next_line.startswith("{{")
            ):
                break
            paragraph_lines.append(next_line)
            i += 1
        blocks.append(f"<p>{inline_markdown(' '.join(paragraph_lines))}</p>")
    return "\n".join(blocks)


def manuscript_edit_link(path: Path, rel: str = "..") -> str:
    return ""


def page_feedback_link(page_no: str, title: str, file_name: str) -> str:
    issue_title = quote(f"[의견] {page_no}. {title}", safe="")
    issue_body = quote(
        "\n".join(
            [
                f"대상 절: {page_no}. {title}",
                f"파일: {file_name}",
                "",
                "남기고 싶은 의견:",
                "",
                "근거 자료나 추가로 살펴볼 질문이 있으면 함께 적어주세요.",
            ]
        ),
        safe="",
    )
    href = f"{GITHUB_REPO_URL}/issues/new?title={issue_title}&body={issue_body}&labels=reader-feedback"
    return f"""<div class="manuscript-actions page-feedback-actions">
    <span class="readonly-note">공개본은 읽기 전용입니다.</span>
    <a class="manuscript-edit-button feedback-button" href="{esc(href)}" target="_blank" rel="noopener">이 절에 의견 남기기</a>
  </div>"""


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def write_csv(df: pd.DataFrame, filename: str) -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)
    df.to_csv(DERIVED / filename, index=False, encoding="utf-8-sig")


def build_derived_data() -> dict[str, list[dict[str, object]]]:
    charts: dict[str, list[dict[str, object]]] = {}

    source_dir = DATA / "source"

    living_path = source_dir / "living_population_2025q3_status.xlsx"
    if living_path.exists():
        living = pd.read_excel(living_path, sheet_name=0, header=[0, 1])
        living.columns = [
            "month",
            "sido",
            "sigungu",
            "component",
            "sex_total",
            "male",
            "female",
            "age_total",
            "under20",
            "age20s",
            "age30s",
            "age40s",
            "age50s",
            "age60s",
            "age70plus",
        ]
        living = living.dropna(subset=["month", "sido", "sigungu", "component"])
        living["month"] = pd.to_numeric(living["month"], errors="coerce").astype("Int64")
        for col in ["sex_total", "male", "female", "age_total", "under20", "age20s", "age30s", "age40s", "age50s", "age60s", "age70plus"]:
            living[col] = pd.to_numeric(living[col], errors="coerce")
        living_pivot = (
            living.pivot_table(
                index=["month", "sido", "sigungu"],
                columns="component",
                values="sex_total",
                aggfunc="sum",
            )
            .reset_index()
            .rename(
                columns={
                    "계": "living_population",
                    "주민등록인구": "registered_population",
                    "체류인구": "stay_population",
                    "외국인": "foreign_population",
                }
            )
        )
        living_summary = (
            living_pivot.groupby(["sido", "sigungu"], as_index=False)[
                ["living_population", "registered_population", "stay_population", "foreign_population"]
            ]
            .mean()
            .fillna(0)
        )
        living_summary["region"] = living_summary["sido"].astype(str) + " " + living_summary["sigungu"].astype(str)
        living_summary["living_registered_ratio"] = np.where(
            living_summary["registered_population"] > 0,
            living_summary["living_population"] / living_summary["registered_population"],
            np.nan,
        )
        living_summary["stay_share_pct"] = np.where(
            living_summary["living_population"] > 0,
            living_summary["stay_population"] / living_summary["living_population"] * 100,
            np.nan,
        )
        living_summary["foreign_share_pct"] = np.where(
            living_summary["living_population"] > 0,
            living_summary["foreign_population"] / living_summary["living_population"] * 100,
            np.nan,
        )
        for col in ["living_population", "registered_population", "stay_population", "foreign_population"]:
            living_summary[f"{col}_10k"] = living_summary[col] / 10000
        living_summary = living_summary.sort_values("living_registered_ratio", ascending=False)
        write_csv(living_summary, "living_population_2025q3_summary.csv")
        charts["living_population_ratio_top"] = living_summary.to_dict("records")

        slope_bridge_path = DERIVED / "sigungu_population_trend_map_values.csv"
        if slope_bridge_path.exists():
            sido_prefix_map = {
                "서울특별시": "11",
                "부산광역시": "26",
                "대구광역시": "27",
                "인천광역시": "28",
                "광주광역시": "29",
                "대전광역시": "30",
                "울산광역시": "31",
                "세종특별자치시": "36",
                "경기도": "41",
                "강원특별자치도": "51",
                "충청북도": "43",
                "충청남도": "44",
                "전북특별자치도": "52",
                "전라남도": "46",
                "경상북도": "47",
                "경상남도": "48",
                "제주특별자치도": "50",
            }
            living_for_map = living_summary.copy()
            living_for_map["kosis_prefix"] = living_for_map["sido"].map(sido_prefix_map)
            living_for_map.loc[
                (living_for_map["sido"] == "대구광역시") & (living_for_map["sigungu"] == "군위군"),
                "kosis_prefix",
            ] = "47"
            bridge = pd.read_csv(slope_bridge_path, dtype=str)
            bridge["kosis_prefix"] = bridge["C1"].astype(str).str[:2]
            bridge_cols = ["topo_code", "topo_name", "C1", "C1_NM", "kosis_prefix"]
            living_map_values = bridge[bridge_cols].merge(
                living_for_map,
                left_on=["kosis_prefix", "C1_NM"],
                right_on=["kosis_prefix", "sigungu"],
                how="left",
            )
            living_map_values["has_living_population"] = living_map_values["living_population"].notna()
            numeric_cols = [
                "living_population",
                "registered_population",
                "stay_population",
                "foreign_population",
                "living_registered_ratio",
                "stay_share_pct",
                "foreign_share_pct",
                "living_population_10k",
                "registered_population_10k",
                "stay_population_10k",
                "foreign_population_10k",
            ]
            for col in numeric_cols:
                if col in living_map_values:
                    living_map_values[col] = pd.to_numeric(living_map_values[col], errors="coerce")
            write_csv(living_map_values, "living_population_2025q3_map_values.csv")
            charts["living_population_ratio_map"] = living_map_values.to_dict("records")

        component_labels = {
            "계": "생활인구 전체",
            "주민등록인구": "주민등록인구",
            "체류인구": "체류인구",
            "외국인": "외국인",
        }
        component_order = ["생활인구 전체", "주민등록인구", "체류인구", "외국인"]
        age_labels = {
            "under20": "20세 미만",
            "age20s": "20대",
            "age30s": "30대",
            "age40s": "40대",
            "age50s": "50대",
            "age60s": "60대",
            "age70plus": "70세 이상",
        }
        monthly_component = (
            living.groupby(["month", "component"], as_index=False)[
                ["sex_total", "male", "female", *age_labels.keys()]
            ]
            .sum()
            .assign(component_label=lambda df: df["component"].map(component_labels))
        )
        monthly_component = monthly_component[monthly_component["component_label"].notna()].copy()
        component_summary = (
            monthly_component.groupby(["component", "component_label"], as_index=False)[
                ["sex_total", "male", "female", *age_labels.keys()]
            ]
            .mean()
        )
        component_summary["component_order"] = component_summary["component_label"].map(
            {name: order for order, name in enumerate(component_order)}
        )

        age_records = []
        for _, row in component_summary.iterrows():
            denominator = row["sex_total"] if row["sex_total"] else np.nan
            for age_col, age_label in age_labels.items():
                value = row[age_col]
                age_records.append(
                    {
                        "component": row["component"],
                        "component_label": row["component_label"],
                        "component_order": row["component_order"],
                        "age_group": age_label,
                        "age_order": list(age_labels).index(age_col),
                        "population": value,
                        "population_10k": value / 10000,
                        "share_pct": value / denominator * 100 if denominator and not pd.isna(denominator) else np.nan,
                    }
                )
        living_age_component = pd.DataFrame(age_records)
        write_csv(living_age_component, "living_population_2025q3_age_component.csv")
        charts["living_population_age_component"] = living_age_component.to_dict("records")

        sex_records = []
        for _, row in component_summary.iterrows():
            denominator = row["sex_total"] if row["sex_total"] else np.nan
            for sex_key, sex_label in [("male", "남성"), ("female", "여성")]:
                value = row[sex_key]
                sex_records.append(
                    {
                        "component": row["component"],
                        "component_label": row["component_label"],
                        "component_order": row["component_order"],
                        "sex": sex_label,
                        "population": value,
                        "population_10k": value / 10000,
                        "share_pct": value / denominator * 100 if denominator and not pd.isna(denominator) else np.nan,
                    }
                )
        living_sex_component = pd.DataFrame(sex_records)
        write_csv(living_sex_component, "living_population_2025q3_sex_component.csv")
        charts["living_population_sex_component"] = living_sex_component.to_dict("records")

        living_monthly_trend = monthly_component[
            ["month", "component", "component_label", "sex_total", "male", "female", *age_labels.keys()]
        ].copy()
        living_monthly_trend["component_order"] = living_monthly_trend["component_label"].map(
            {name: order for order, name in enumerate(component_order)}
        )
        living_monthly_trend["month_label"] = living_monthly_trend["month"].astype(str).str.replace(
            r"^(\d{4})(\d{2})$", r"\1.\2", regex=True
        )
        living_monthly_trend["population"] = living_monthly_trend["sex_total"]
        living_monthly_trend["population_10k"] = living_monthly_trend["population"] / 10000
        living_monthly_trend = living_monthly_trend.sort_values(["component_order", "month"])
        write_csv(living_monthly_trend, "living_population_2025q3_monthly_trend.csv")
        charts["living_population_monthly_trend"] = living_monthly_trend.to_dict("records")

    mobile_inflow_path = source_dir / "mobile_inflow_sigungu_20260426.xlsx"
    if mobile_inflow_path.exists():
        mobile = pd.read_excel(mobile_inflow_path, sheet_name=3)
        mobile.columns = ["sido", "sigungu", "week_label", "inside", "outside", "total"]
        mobile = mobile.dropna(subset=["sido", "sigungu", "week_label"])
        for col in ["inside", "outside", "total"]:
            mobile[col] = pd.to_numeric(mobile[col], errors="coerce")
        week_parts = mobile["week_label"].astype(str).str.extract(r"(?P<year>\d{4})\.(?P<month>\d{2})\.(?P<week>\d+)주차")
        mobile["year"] = pd.to_numeric(week_parts["year"], errors="coerce").astype("Int64")
        mobile["month"] = pd.to_numeric(week_parts["month"], errors="coerce").astype("Int64")
        mobile["week_in_month"] = pd.to_numeric(week_parts["week"], errors="coerce").astype("Int64")
        mobile["region"] = mobile["sido"].astype(str) + " " + mobile["sigungu"].astype(str)
        mobile_2025 = mobile[mobile["year"] == 2025].copy()
        mobile_summary = (
            mobile_2025.groupby(["sido", "sigungu", "region"], as_index=False)
            .agg(
                weeks=("week_label", "nunique"),
                avg_inside=("inside", "mean"),
                avg_outside=("outside", "mean"),
                avg_total=("total", "mean"),
            )
            .fillna(0)
        )
        mobile_summary["outside_share_pct"] = np.where(
            mobile_summary["avg_total"] > 0,
            mobile_summary["avg_outside"] / mobile_summary["avg_total"] * 100,
            np.nan,
        )
        for col in ["avg_inside", "avg_outside", "avg_total"]:
            mobile_summary[f"{col}_10k"] = mobile_summary[col] / 10000
        mobile_summary = mobile_summary.sort_values("avg_total", ascending=False)
        write_csv(mobile_summary, "mobile_inflow_sigungu_2025_summary.csv")
        charts["mobile_inflow_top_sigungu"] = mobile_summary.to_dict("records")

        mobile_sex = pd.read_excel(mobile_inflow_path, sheet_name=0)
        mobile_sex.columns = ["group_type", "group", "week_label", "inside", "outside", "total"]
        mobile_sex = mobile_sex.dropna(subset=["group_type", "group", "week_label"])
        type_values = list(mobile_sex["group_type"].dropna().drop_duplicates())
        group_values = list(mobile_sex["group"].dropna().drop_duplicates())
        if len(type_values) >= 2 and len(group_values) >= 3:
            sex_type = type_values[1]
            male_value = group_values[1]
            female_value = group_values[2]
            mobile_sex = mobile_sex[
                (mobile_sex["group_type"] == sex_type)
                & (mobile_sex["group"].isin([male_value, female_value]))
            ].copy()
            mobile_sex["sex"] = mobile_sex["group"].map({male_value: "남성", female_value: "여성"})
            for col in ["inside", "outside", "total"]:
                mobile_sex[col] = pd.to_numeric(mobile_sex[col], errors="coerce")
            week_parts = mobile_sex["week_label"].astype(str).str.extract(r"(?P<year>\d{4})\.(?P<month>\d{2})\.(?P<week>\d+)")
            mobile_sex["year"] = pd.to_numeric(week_parts["year"], errors="coerce").astype("Int64")
            mobile_sex["month"] = pd.to_numeric(week_parts["month"], errors="coerce").astype("Int64")
            sex_trend = (
                mobile_sex.dropna(subset=["year", "sex"])
                .groupby(["year", "sex"], as_index=False)
                .agg(
                    weeks=("week_label", "nunique"),
                    avg_inside=("inside", "mean"),
                    avg_outside=("outside", "mean"),
                    avg_total=("total", "mean"),
                )
            )
            sex_trend["outside_share_pct"] = np.where(
                sex_trend["avg_total"] > 0,
                sex_trend["avg_outside"] / sex_trend["avg_total"] * 100,
                np.nan,
            )
            sex_trend["avg_outside_100m"] = sex_trend["avg_outside"] / 1000000
            sex_trend["avg_total_100m"] = sex_trend["avg_total"] / 1000000
            base = sex_trend[sex_trend["year"] == sex_trend["year"].min()][["sex", "avg_outside"]].rename(
                columns={"avg_outside": "base_avg_outside"}
            )
            sex_trend = sex_trend.merge(base, on="sex", how="left")
            sex_trend["outside_index_first_year_100"] = np.where(
                sex_trend["base_avg_outside"] > 0,
                sex_trend["avg_outside"] / sex_trend["base_avg_outside"] * 100,
                np.nan,
            )
            sex_trend["year_label"] = sex_trend["year"].astype(str)
            sex_trend.loc[sex_trend["year"] == 2026, "year_label"] = "2026(4월까지)"
            sex_trend = sex_trend.sort_values(["sex", "year"])
            write_csv(sex_trend, "mobile_outside_migration_by_sex.csv")
            charts["mobile_outside_migration_by_sex"] = sex_trend.to_dict("records")

    policy_typology = pd.DataFrame(
        [
            {
                "order": 1,
                "category": "현금·세제 지원",
                "mechanism": "출산과 양육의 직접 비용을 낮춘다.",
                "representative_tools": "첫만남이용권, 부모급여, 아동수당, 지자체 출산장려금, 세액공제",
                "evaluation_question": "지원금이 출생 결정에 영향을 주었는가, 아니면 기존 출생가구의 비용을 보전했는가",
            },
            {
                "order": 2,
                "category": "시간 지원과 소득보전",
                "mechanism": "부모가 일을 잃지 않고 임신·출산·육아 시간을 확보하게 한다.",
                "representative_tools": "출산전후휴가, 배우자 출산휴가, 육아휴직, 육아기 근로시간 단축, 대체인력 지원",
                "evaluation_question": "제도를 쓸 수 있는 노동자와 쓸 수 없는 노동자의 격차가 줄었는가",
            },
            {
                "order": 3,
                "category": "돌봄·교육 서비스",
                "mechanism": "가정 안의 돌봄 부담을 사회적 서비스로 분산한다.",
                "representative_tools": "국공립 어린이집, 보육료 지원, 아이돌봄서비스, 늘봄학교, 유보통합",
                "evaluation_question": "부모가 실제 생활권에서 필요한 시간에 믿고 맡길 수 있는가",
            },
            {
                "order": 4,
                "category": "주거와 결혼 지원",
                "mechanism": "가족 형성의 가장 큰 고정비인 주거 불안을 낮춘다.",
                "representative_tools": "신혼·출산가구 공공주택, 전세·구입자금 대출, 청년·신혼부부 주거지원",
                "evaluation_question": "혼인과 출산 연령층이 일자리 가까운 곳에 안정적으로 살 수 있는가",
            },
            {
                "order": 5,
                "category": "임신·난임·건강 지원",
                "mechanism": "아이를 원하지만 의료·건강 장벽을 겪는 가구를 지원한다.",
                "representative_tools": "난임시술비 지원, 임신·출산 진료비, 산모·신생아 건강관리, 고위험 임산부 지원",
                "evaluation_question": "정책 대상의 접근성과 성공률, 사후 돌봄이 함께 개선되었는가",
            },
            {
                "order": 6,
                "category": "지역 정주 지원",
                "mechanism": "출생 이후 가족이 지역에 남을 생활 조건을 만든다.",
                "representative_tools": "지자체 양육수당, 지역 돌봄 인프라, 소아의료, 교육·교통·일자리 연계",
                "evaluation_question": "태어난 아이가 4년 뒤에도 그 지역에 남아 있는가",
            },
            {
                "order": 7,
                "category": "거버넌스와 구조개혁",
                "mechanism": "부처별 사업을 묶고 장기 성과를 관리한다.",
                "representative_tools": "저출산고령사회 기본계획, 저출산고령사회위원회, 인구전략기획부 논의, 성과평가",
                "evaluation_question": "사업 수와 예산이 아니라 실제 삶의 조건 변화로 평가하고 있는가",
            },
        ]
    )
    write_csv(policy_typology, "low_fertility_policy_typology.csv")
    charts["low_fertility_policy_typology"] = policy_typology.to_dict("records")

    international_policy_success = pd.DataFrame(
        [
            {
                "country": "한국",
                "policy_model": "종합 패키지형",
                "main_tools": "현금지원, 부모급여·아동수당, 육아휴직, 보육, 신혼·출산가구 주거지원",
                "policy_turning_year": 2006,
                "start_year": 2006,
                "tfr_start": 1.13,
                "peak_year": 2015,
                "tfr_peak": 1.24,
                "latest_year": 2024,
                "tfr_latest": 0.75,
                "change_start_to_latest": -0.38,
                "assessment": "재정투입은 컸지만 출산율 회복에는 실패했고, 2024년의 반등도 구조적 전환으로 보기는 이르다.",
            },
            {
                "country": "싱가포르",
                "policy_model": "고비용 보전·주거 연계형",
                "main_tools": "Baby Bonus, CDA 공동저축, 육아휴직, 보육보조, HDB 주거·결혼 패키지",
                "policy_turning_year": 2001,
                "start_year": 2001,
                "tfr_start": 1.41,
                "peak_year": 2012,
                "tfr_peak": 1.29,
                "latest_year": 2025,
                "tfr_latest": 0.87,
                "change_start_to_latest": -0.54,
                "assessment": "매우 촘촘한 지원에도 초저출산을 되돌리지 못했다. 비용 보전은 필요조건이지만 충분조건이 아니다.",
            },
            {
                "country": "헝가리",
                "policy_model": "혼인·주거·세제 집중형",
                "main_tools": "가족세액공제, 다자녀 모성 소득세 면제, Baby-expecting loan, CSOK·CSOK Plus 주거대출",
                "policy_turning_year": 2011,
                "start_year": 2011,
                "tfr_start": 1.23,
                "peak_year": 2021,
                "tfr_peak": 1.61,
                "latest_year": 2024,
                "tfr_latest": 1.40,
                "change_start_to_latest": 0.17,
                "assessment": "일정한 반등은 있었지만 대체수준에는 멀고 최근에는 다시 약화되었다. 성과와 비용, 계층 편향을 함께 보아야 한다.",
            },
            {
                "country": "일본",
                "policy_model": "아동정책 제도화·일가정양립형",
                "main_tools": "아동수당 확대, 보육 확충, 남성육아휴직, 고등교육 지원, 어린이미래전략",
                "policy_turning_year": 1994,
                "start_year": 1994,
                "tfr_start": 1.50,
                "peak_year": 2015,
                "tfr_peak": 1.45,
                "latest_year": 2024,
                "tfr_latest": 1.15,
                "change_start_to_latest": -0.35,
                "assessment": "제도는 넓어졌지만 혼인 지연, 청년소득, 직장문화 문제를 충분히 넘지 못해 출산율은 계속 낮아졌다.",
            },
        ]
    )
    international_policy_success["peak_minus_start"] = (
        international_policy_success["tfr_peak"] - international_policy_success["tfr_start"]
    ).round(2)
    international_policy_success["latest_minus_peak"] = (
        international_policy_success["tfr_latest"] - international_policy_success["tfr_peak"]
    ).round(2)
    write_csv(international_policy_success, "pronatalist_policy_country_comparison.csv")
    charts["pronatalist_policy_country_comparison"] = international_policy_success.to_dict("records")

    low_fertility_budget = pd.DataFrame(
        [
            {"year": 2020, "broad_budget_trillion_krw": 40.2, "direct_budget_trillion_krw": 22.1},
            {"year": 2021, "broad_budget_trillion_krw": 47.2, "direct_budget_trillion_krw": 20.3},
            {"year": 2022, "broad_budget_trillion_krw": 50.6, "direct_budget_trillion_krw": 21.1},
            {"year": 2023, "broad_budget_trillion_krw": 47.0, "direct_budget_trillion_krw": 23.5},
            {"year": 2024, "broad_budget_trillion_krw": 49.0, "direct_budget_trillion_krw": 25.3},
            {"year": 2025, "broad_budget_trillion_krw": 53.1, "direct_budget_trillion_krw": 28.6},
        ]
    )
    low_fertility_budget["direct_share_pct"] = (
        low_fertility_budget["direct_budget_trillion_krw"]
        / low_fertility_budget["broad_budget_trillion_krw"]
        * 100
    ).round(1)
    write_csv(low_fertility_budget, "low_fertility_budget_trend.csv")
    charts["low_fertility_budget_trend"] = low_fertility_budget.to_dict("records")

    major_budget_2026 = pd.DataFrame(
        [
            {
                "field": "일·가정양립",
                "budget_2025_100m_krw": 43517,
                "budget_2026_100m_krw": 44299,
                "increase_100m_krw": 782,
            },
            {
                "field": "양육·돌봄",
                "budget_2025_100m_krw": 24773,
                "budget_2026_100m_krw": 36042,
                "increase_100m_krw": 11269,
            },
            {
                "field": "주거",
                "budget_2025_100m_krw": 38669,
                "budget_2026_100m_krw": 62064,
                "increase_100m_krw": 23395,
            },
        ]
    )
    for column in ["budget_2025_100m_krw", "budget_2026_100m_krw", "increase_100m_krw"]:
        major_budget_2026[column.replace("_100m_krw", "_trillion_krw")] = (
            major_budget_2026[column] / 10000
        ).round(3)
    write_csv(major_budget_2026, "low_fertility_major_budget_2026.csv")
    charts["low_fertility_major_budget_2026"] = major_budget_2026.to_dict("records")

    housing_budget = major_budget_2026[major_budget_2026["field"] == "주거"].copy()
    housing_support_policy_budget = pd.DataFrame(
        [
            {
                "year": 2025,
                "housing_budget_trillion_krw": float(housing_budget["budget_2025_trillion_krw"].iloc[0]),
                "total_major_budget_trillion_krw": float(major_budget_2026["budget_2025_trillion_krw"].sum()),
            },
            {
                "year": 2026,
                "housing_budget_trillion_krw": float(housing_budget["budget_2026_trillion_krw"].iloc[0]),
                "total_major_budget_trillion_krw": float(major_budget_2026["budget_2026_trillion_krw"].sum()),
            },
        ]
    )
    housing_support_policy_budget["housing_share_pct"] = (
        housing_support_policy_budget["housing_budget_trillion_krw"]
        / housing_support_policy_budget["total_major_budget_trillion_krw"]
        * 100
    ).round(1)
    write_csv(housing_support_policy_budget, "housing_support_policy_budget.csv")
    charts["housing_support_policy_budget"] = housing_support_policy_budget.to_dict("records")

    for chart_id, filename in [
        ("housing_tenure_young_newlywed", "housing_tenure_young_newlywed.csv"),
        ("housing_finance_burden_by_age", "housing_finance_burden_by_age.csv"),
        ("youth_housing_consumption_pressure", "youth_housing_consumption_pressure.csv"),
        ("housing_security_outcomes_national", "housing_security_outcomes_national.csv"),
        ("capital_region_housing_marriage_birth", "capital_region_housing_marriage_birth.csv"),
        ("housing_security_outcome_regression", "housing_security_outcome_regression.csv"),
    ]:
        path = DERIVED / filename
        if path.exists():
            chart_df = pd.read_csv(path)
            write_csv(chart_df, filename)
            charts[chart_id] = chart_df.to_dict("records")

    international_housing_cases = pd.DataFrame(
        [
            {
                "country": "한국",
                "tfr_year": 2024,
                "total_fertility_rate": 0.75,
                "housing_context": "수도권 청년·신혼 주거비 부담과 자가 진입 지연",
                "policy_reading": "주거지원은 필요하지만 교육비·노동시장·돌봄 부담과 분리하면 효과가 제한된다.",
            },
            {
                "country": "싱가포르",
                "tfr_year": 2024,
                "total_fertility_rate": 0.97,
                "housing_context": "거주가구 약 80%가 HDB 공공주택에 거주하고 자가점유율도 매우 높다.",
                "policy_reading": "강한 주거지원만으로는 긴 노동시간, 높은 양육비, 결혼·출산 지연을 넘기 어렵다.",
            },
            {
                "country": "프랑스",
                "tfr_year": 2024,
                "total_fertility_rate": 1.62,
                "housing_context": "출산율은 하락했지만 가족수당·보육·주거수당이 결합된 정책 체계가 남아 있다.",
                "policy_reading": "주거비 보조는 보육과 소득지원, 비혼·동거 가족 포괄성과 함께 작동할 때 완충 효과가 커진다.",
            },
            {
                "country": "이스라엘",
                "tfr_year": 2023,
                "total_fertility_rate": 2.85,
                "housing_context": "OECD가 집값 상승 압력이 큰 국가로 분류하지만 출산율은 대체수준을 넘는다.",
                "policy_reading": "높은 출산율은 주거비만으로 설명되지 않으며 가족규범, 종교·공동체, 청년 가족형성 문화가 함께 작동한다.",
            },
        ]
    )
    write_csv(international_housing_cases, "international_housing_fertility_cases.csv")
    charts["international_housing_fertility_cases"] = international_housing_cases.to_dict("records")

    def read_education_csv(name: str) -> pd.DataFrame:
        df = pd.read_csv(DATA / name)
        df["year"] = pd.to_numeric(df["PRD_DE"], errors="coerce").astype("Int64")
        df["value"] = pd.to_numeric(df["DT"], errors="coerce")
        df["ITM_NM"] = df["ITM_NM"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
        df["C1_NM"] = df["C1_NM"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
        if "C2_NM" in df.columns:
            df["C2_NM"] = df["C2_NM"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
        return df

    edu_total = read_education_csv("education_DT_1PE003.csv")
    edu_cost = read_education_csv("education_DT_1PE201.csv")
    edu_participation = read_education_csv("education_DT_1PE301.csv")
    edu_time = read_education_csv("education_DT_1PE103.csv")
    edu_income_cost = read_education_csv("education_DT_1PE209.csv")
    edu_income_participation = read_education_csv("education_DT_1PE309.csv")

    def series_from_education(
        df: pd.DataFrame,
        *,
        item: str,
        category: str,
        value_name: str,
    ) -> pd.DataFrame:
        out = df[(df["ITM_NM"] == item) & (df["C1_NM"] == category)][["year", "value"]].dropna()
        return out.rename(columns={"value": value_name}).sort_values("year")

    private_total = series_from_education(
        edu_total, item="전체", category="전체", value_name="private_education_total_100m_krw"
    )
    private_total["private_education_total_trillion_krw"] = (
        private_total["private_education_total_100m_krw"] / 10000
    ).round(3)
    private_monthly = series_from_education(
        edu_cost, item="평 균", category="사교육비", value_name="monthly_private_education_10k_krw"
    )
    private_participation = series_from_education(
        edu_participation, item="평 균", category="사교육 참여", value_name="private_education_participation_rate"
    )
    private_hours = series_from_education(
        edu_time, item="평 균", category="전체", value_name="weekly_private_education_hours"
    )
    private_trend = private_total.merge(private_monthly, on="year", how="outer")
    private_trend = private_trend.merge(private_participation, on="year", how="outer")
    private_trend = private_trend.merge(private_hours, on="year", how="outer").sort_values("year")
    private_trend["monthly_private_education_krw"] = (
        private_trend["monthly_private_education_10k_krw"] * 10000
    ).round(0)
    base_2007 = private_trend[private_trend["year"] == 2007].iloc[0]
    for col in [
        "private_education_total_trillion_krw",
        "monthly_private_education_10k_krw",
        "private_education_participation_rate",
        "weekly_private_education_hours",
    ]:
        private_trend[f"{col}_index_2007_100"] = (private_trend[col] / base_2007[col] * 100).round(2)
    write_csv(private_trend, "private_education_cost_trend.csv")
    charts["private_education_cost_trend"] = private_trend.to_dict("records")

    levels = ["평 균", "초등학교", "중학교", "고등학교"]
    school_cost = edu_cost[(edu_cost["ITM_NM"].isin(levels)) & (edu_cost["C1_NM"] == "사교육비")][
        ["year", "ITM_NM", "value"]
    ].rename(columns={"ITM_NM": "school_level", "value": "monthly_private_education_10k_krw"})
    school_participation = edu_participation[
        (edu_participation["ITM_NM"].isin(levels)) & (edu_participation["C1_NM"] == "사교육 참여")
    ][["year", "ITM_NM", "value"]].rename(
        columns={"ITM_NM": "school_level", "value": "private_education_participation_rate"}
    )
    school = school_cost.merge(school_participation, on=["year", "school_level"], how="outer")
    school["school_level"] = pd.Categorical(school["school_level"], categories=levels, ordered=True)
    school = school.sort_values(["year", "school_level"])
    write_csv(school, "private_education_school_level.csv")
    charts["private_education_school_level"] = school.to_dict("records")

    high_school_driver_items = {
        "사교육 참여": "전체 참여율",
        "과목: 일반교과 사교육": "일반교과",
        "수학": "수학",
        "영어": "영어",
        "국어": "국어",
        "사회 과학": "사회·과학",
        "유료인터넷 및 통신강좌 등": "유료인터넷·통신강좌",
        "과목: 진로·진학 학습상담": "진로·진학 학습상담",
    }
    high_school_drivers = edu_participation[
        (edu_participation["ITM_NM"] == "고등학교") & (edu_participation["C1_NM"].isin(high_school_driver_items))
    ][["year", "C1_NM", "value"]].rename(columns={"C1_NM": "item", "value": "participation_rate"})
    high_school_drivers["item_label"] = high_school_drivers["item"].map(high_school_driver_items)
    high_school_drivers = high_school_drivers.sort_values(["item_label", "year"])
    base_2019 = high_school_drivers[high_school_drivers["year"] == 2019][["item_label", "participation_rate"]].rename(
        columns={"participation_rate": "base_2019_participation_rate"}
    )
    high_school_drivers = high_school_drivers.merge(base_2019, on="item_label", how="left")
    high_school_drivers["change_from_2019_p"] = (
        high_school_drivers["participation_rate"] - high_school_drivers["base_2019_participation_rate"]
    ).round(2)
    write_csv(high_school_drivers, "high_school_private_education_drivers.csv")
    charts["high_school_private_education_drivers"] = high_school_drivers.to_dict("records")

    income_order = [
        "300만원 미만",
        "300 ~400만원 미만",
        "400 ~500만원 미만",
        "500 ~600만원 미만",
        "600 ~700만원 미만",
        "- 700 ~ 800만원 미만",
        "-800~ 1000만원 미만",
        "-1000만원 이상",
    ]
    income_label = {
        "300만원 미만": "300만원 미만",
        "300 ~400만원 미만": "300-400만원",
        "400 ~500만원 미만": "400-500만원",
        "500 ~600만원 미만": "500-600만원",
        "600 ~700만원 미만": "600-700만원",
        "- 700 ~ 800만원 미만": "700-800만원",
        "-800~ 1000만원 미만": "800-1,000만원",
        "-1000만원 이상": "1,000만원 이상",
    }
    latest_income_year = int(edu_income_cost["year"].dropna().max())
    income_cost = edu_income_cost[
        (edu_income_cost["year"] == latest_income_year)
        & (edu_income_cost["C1_NM"] == "사교육비")
        & (edu_income_cost["ITM_NM"].isin(income_order))
    ][["year", "ITM_NM", "value"]].rename(columns={"ITM_NM": "income_group", "value": "monthly_private_education_10k_krw"})
    income_participation = edu_income_participation[
        (edu_income_participation["year"] == latest_income_year)
        & (edu_income_participation["C1_NM"] == "사교육 참여")
        & (edu_income_participation["ITM_NM"].isin(income_order))
    ][["year", "ITM_NM", "value"]].rename(
        columns={"ITM_NM": "income_group", "value": "private_education_participation_rate"}
    )
    income_gap = income_cost.merge(income_participation, on=["year", "income_group"], how="outer")
    income_gap["income_group_label"] = income_gap["income_group"].map(income_label)
    income_gap["sort_order"] = income_gap["income_group"].map({name: idx for idx, name in enumerate(income_order)})
    income_gap = income_gap.sort_values("sort_order")
    low = income_gap[income_gap["income_group"] == "300만원 미만"].iloc[0]
    high = income_gap[income_gap["income_group"] == "-1000만원 이상"].iloc[0]
    income_gap["spending_gap_vs_low_10k_krw"] = (
        income_gap["monthly_private_education_10k_krw"] - low["monthly_private_education_10k_krw"]
    ).round(2)
    income_gap["participation_gap_vs_low_pctp"] = (
        income_gap["private_education_participation_rate"] - low["private_education_participation_rate"]
    ).round(2)
    income_gap["high_low_spending_ratio"] = round(
        high["monthly_private_education_10k_krw"] / low["monthly_private_education_10k_krw"], 2
    )
    write_csv(income_gap, "private_education_income_gap.csv")
    charts["private_education_income_gap"] = income_gap.to_dict("records")

    newlywed_raw_path = DATA / "kosis_newlywed_income_children_DT_1NW2016.csv"
    if newlywed_raw_path.exists():
        newlywed_raw = pd.read_csv(newlywed_raw_path)
        newlywed_raw["year"] = pd.to_numeric(newlywed_raw["PRD_DE"], errors="coerce").astype("Int64")
        newlywed_raw["value"] = pd.to_numeric(newlywed_raw["DT"], errors="coerce")
        income_order_newlywed = [
            "합계",
            "1천만원 미만",
            "1천만원~3천만원 미만",
            "3천만원~5천만원 미만",
            "5천만원~7천만원 미만",
            "7천만원~1억원 미만",
            "1억원 이상",
        ]
        newlywed = (
            newlywed_raw[
                newlywed_raw["C1_NM"].isin(income_order_newlywed)
                & newlywed_raw["C2_NM"].isin(["자녀 없음", "자녀 있음", "1명", "2명", "3명 이상", "평균출생아 수"])
            ]
            .pivot_table(index=["year", "C1_NM"], columns="C2_NM", values="value", aggfunc="first")
            .reset_index()
            .rename(
                columns={
                    "C1_NM": "income_group",
                    "자녀 없음": "no_child_pct",
                    "자녀 있음": "has_child_pct",
                    "1명": "one_child_pct",
                    "2명": "two_child_pct",
                    "3명 이상": "three_plus_child_pct",
                    "평균출생아 수": "avg_births",
                }
            )
        )
        newlywed["income_group"] = pd.Categorical(newlywed["income_group"], categories=income_order_newlywed, ordered=True)
        newlywed = newlywed.sort_values(["year", "income_group"])
        latest_newlywed_year = int(newlywed["year"].dropna().max())
        latest_newlywed = newlywed[newlywed["year"] == latest_newlywed_year].copy()
        total_row = latest_newlywed[latest_newlywed["income_group"].astype(str).eq("합계")].iloc[0]
        newlywed["latest_year"] = latest_newlywed_year
        newlywed["latest_total_avg_births"] = float(total_row["avg_births"])
        newlywed["latest_total_no_child_pct"] = float(total_row["no_child_pct"])
        write_csv(newlywed, "newlywed_income_fertility.csv")
        charts["newlywed_income_fertility"] = newlywed.to_dict("records")

    pop_for_education = pd.read_csv(DATA / "population_projection_indicators.csv")
    pop_for_education["DT"] = pd.to_numeric(pop_for_education["DT"], errors="coerce")
    pop_for_education["PRD_DE"] = pd.to_numeric(pop_for_education["PRD_DE"], errors="coerce")
    pop_mid = pop_for_education[
        (pop_for_education["C1_NM"].astype(str).str.contains("중위"))
        & (pop_for_education["C2_NM"] == "전국")
    ]
    pop_pivot = pop_mid[
        pop_mid["C3_NM"].isin(["총인구(명)", "- 구성비(%): 0-14세", "- 구성비(%): 15-64세"])
    ].pivot_table(index="PRD_DE", columns="C3_NM", values="DT", aggfunc="first").reset_index()
    pop_pivot = pop_pivot.rename(
        columns={
            "PRD_DE": "year",
            "총인구(명)": "total_population",
            "- 구성비(%): 0-14세": "child_share",
            "- 구성비(%): 15-64세": "working_share",
        }
    )
    pop_pivot["school_age_proxy_0_14"] = pop_pivot["total_population"] * pop_pivot["child_share"] / 100
    pressure_edu = private_trend.merge(pop_pivot[["year", "school_age_proxy_0_14"]], on="year", how="left")
    pressure_edu = pressure_edu[pressure_edu["year"].between(2007, 2025)].copy()
    for col in [
        "school_age_proxy_0_14",
        "private_education_total_trillion_krw",
        "monthly_private_education_10k_krw",
        "private_education_participation_rate",
    ]:
        base_value = pressure_edu.loc[pressure_edu["year"] == 2007, col].iloc[0]
        pressure_edu[f"{col}_index_2007_100"] = (pressure_edu[col] / base_value * 100).round(2)
    write_csv(pressure_edu, "school_age_private_education_pressure.csv")
    charts["school_age_private_education_pressure"] = pressure_edu.to_dict("records")

    burden = read_education_csv("education_DT_1SSED100R.csv")
    burden_items = burden.pivot_table(index="year", columns="ITM_NM", values="value", aggfunc="first").reset_index()
    burden_items["education_burden_heavy_or_somewhat_pct"] = (
        burden_items.get("-매우 부담스럽다", 0) + burden_items.get("-약간 부담스럽다", 0)
    ).round(2)
    burden_items["education_burden_not_heavy_pct"] = (
        burden_items.get("-별로 부담스럽지 않다", 0) + burden_items.get("-전혀 부담스럽지 않다", 0)
    ).round(2)
    burden_reason = read_education_csv("education_DT_1SSED110R.csv")
    reason_items = burden_reason.pivot_table(index="year", columns="ITM_NM", values="value", aggfunc="first").reset_index()
    expectation = read_education_csv("education_DT_1SSED080R.csv")
    expectation_items = expectation.pivot_table(index="year", columns="ITM_NM", values="value", aggfunc="first").reset_index()
    expectation_items["expect_university_or_more_pct"] = (
        expectation_items.get("기대교육수준-대학(교)(4년제미만)", 0)
        + expectation_items.get("기대교육수준-대학교(4년제 이상)", 0)
        + expectation_items.get("기대교육수준-대학원(석사)", 0)
        + expectation_items.get("기대교육수준-대학원(박사)", 0)
    ).round(2)
    burden_view = burden_items[
        ["year", "학생 자녀가 있는 가구", "education_burden_heavy_or_somewhat_pct", "education_burden_not_heavy_pct"]
    ].rename(columns={"학생 자녀가 있는 가구": "household_with_student_child_pct"})
    burden_view = burden_view.merge(
        reason_items[["year", "학교 납입금", "학교 납입금 외 교육비"]],
        on="year",
        how="left",
    ).rename(
        columns={
            "학교 납입금": "school_payment_most_burdensome_pct",
            "학교 납입금 외 교육비": "non_school_payment_education_cost_most_burdensome_pct",
        }
    )
    burden_view = burden_view.merge(
        expectation_items[["year", "expect_university_or_more_pct"]],
        on="year",
        how="left",
    ).sort_values("year")
    write_csv(burden_view, "education_burden_perception.csv")
    charts["education_burden_perception"] = burden_view.to_dict("records")

    pop = pd.read_csv(DATA / "population_projection_indicators.csv")
    pop["DT"] = pd.to_numeric(pop["DT"], errors="coerce")
    pop["PRD_DE"] = pd.to_numeric(pop["PRD_DE"], errors="coerce")
    base = pop[(pop["C1_NM"].astype(str).str.contains("중위")) & (pop["C2_NM"] == "전국")]

    age = base[base["C3_NM"].isin(["- 구성비(%): 0-14세", "- 구성비(%): 15-64세", "- 구성비(%): 65세 이상"])]
    age = age.pivot_table(index="PRD_DE", columns="C3_NM", values="DT", aggfunc="first").reset_index()
    age = age.rename(
        columns={
            "PRD_DE": "year",
            "- 구성비(%): 0-14세": "age_0_14_share",
            "- 구성비(%): 15-64세": "age_15_64_share",
            "- 구성비(%): 65세 이상": "age_65_plus_share",
        }
    )
    age = age[age["year"].between(2000, 2072)]
    write_csv(age, "age_composition_projection.csv")
    charts["age_composition_projection"] = age.to_dict("records")

    pressure_items = [
        "총인구(명)",
        "인구성장률(%)",
        "- 구성비(%): 0-14세",
        "- 구성비(%): 15-64세",
        "- 구성비(%): 65세 이상",
        "총부양비",
        "노년부양비",
        "노령화지수",
        "중위연령(세)",
        "중위연령(세)-남자",
        "중위연령(세)-여자",
    ]
    pressure = base[base["C3_NM"].isin(pressure_items)]
    pressure = pressure.pivot_table(index="PRD_DE", columns="C3_NM", values="DT", aggfunc="first").reset_index()
    pressure = pressure.rename(
        columns={
            "PRD_DE": "year",
            "총인구(명)": "total_population",
            "인구성장률(%)": "population_growth_rate",
            "- 구성비(%): 0-14세": "child_share",
            "- 구성비(%): 15-64세": "working_share",
            "- 구성비(%): 65세 이상": "older_share",
            "총부양비": "total_dependency_ratio",
            "노년부양비": "old_age_dependency_ratio",
            "노령화지수": "aging_index",
            "중위연령(세)": "median_age",
            "중위연령(세)-남자": "male_median_age",
            "중위연령(세)-여자": "female_median_age",
        }
    )
    pressure["median_age_gap_female_minus_male"] = pressure["female_median_age"] - pressure["male_median_age"]
    pressure = pressure[pressure["year"].between(2000, 2072)]
    write_csv(pressure, "national_population_pressure.csv")
    charts["national_population_pressure"] = pressure.to_dict("records")

    aging_index_growth = pressure[
        [
            "year",
            "child_share",
            "older_share",
            "aging_index",
            "old_age_dependency_ratio",
            "median_age",
        ]
    ].copy()
    aging_index_growth["aging_index_change_from_2000"] = (
        aging_index_growth["aging_index"] - aging_index_growth.loc[aging_index_growth["year"].idxmin(), "aging_index"]
    ).round(1)
    write_csv(aging_index_growth, "aging_index_growth.csv")
    charts["aging_index_growth"] = aging_index_growth.to_dict("records")

    pyramid_raw = pd.read_csv(DATA / "population_pyramid_raw_DT_1BPA001.csv")
    pyramid_raw["DT"] = pd.to_numeric(pyramid_raw["DT"], errors="coerce")
    pyramid_raw["PRD_DE"] = pd.to_numeric(pyramid_raw["PRD_DE"], errors="coerce")
    age_band_rows = pyramid_raw[
        (pyramid_raw["PRD_DE"].isin([1980, 1990, 2020, 2025]))
        & (pyramid_raw["C1"].astype(str).eq("1"))
        & (pyramid_raw["C2"].astype(str).isin(["1", "2"]))
        & (
            pyramid_raw["C3_NM"].astype(str).str.match(r"^\d+\s*-\s*\d+세$")
            | pyramid_raw["C3_NM"].astype(str).str.match(r"^\d+세\s*이상$")
            | pyramid_raw["C3_NM"].astype(str).str.match(r"^\d+세이상$")
        )
    ].copy()
    age_band_rows["raw_age_start"] = age_band_rows["C3_NM"].astype(str).str.extract(r"^(\d+)")[0].astype(int)
    top_80 = age_band_rows["C3_NM"].astype(str).str.match(r"^80세\s*이상$|^80세이상$")
    age_band_rows = age_band_rows[(age_band_rows["raw_age_start"] < 80) | top_80].copy()
    age_band_rows["age_start"] = age_band_rows["raw_age_start"].where(age_band_rows["raw_age_start"] < 80, 80)
    age_band_rows["age_band"] = age_band_rows["age_start"].map(
        lambda value: "80세 이상" if int(value) >= 80 else f"{int(value)}-{int(value) + 4}세"
    )
    age_band_rows["sex"] = age_band_rows["C2"].astype(str).map({"1": "male", "2": "female"})
    grouped_age = age_band_rows.groupby(["PRD_DE", "age_start", "age_band", "sex"], as_index=False)["DT"].sum()
    pyramid = grouped_age.pivot_table(
        index=["PRD_DE", "age_start", "age_band"],
        columns="sex",
        values="DT",
        aggfunc="first",
    ).reset_index()
    pyramid = pyramid.rename(columns={"PRD_DE": "year"})
    pyramid["male_negative"] = -pyramid["male"]
    pyramid["total"] = pyramid["male"] + pyramid["female"]
    pyramid = pyramid[["year", "age_start", "age_band", "male", "female", "male_negative", "total"]].sort_values(["year", "age_start"])
    write_csv(pyramid, "population_pyramid_5yr_1980_1990_2020_2025.csv")
    charts["population_pyramid_four_panel"] = pyramid.to_dict("records")

    sex = base[base["C3_NM"].isin(["성비(여자1백명당)", "인구성장률(%)"])]
    sex = sex.pivot_table(index="PRD_DE", columns="C3_NM", values="DT", aggfunc="first").reset_index()
    sex = sex.rename(columns={"PRD_DE": "year", "성비(여자1백명당)": "sex_ratio", "인구성장률(%)": "population_growth_rate"})
    sex = sex[sex["year"].between(2000, 2072)]
    write_csv(sex, "sex_ratio_projection.csv")
    charts["sex_ratio_projection"] = sex.to_dict("records")

    measure = pd.read_csv(DATA / "population_measure_comparison.csv")
    for col in ["registered_population", "census_population", "projection_population"]:
        measure[col] = pd.to_numeric(measure[col], errors="coerce")
        measure[f"{col}_million"] = (measure[col] / 1_000_000).round(3)
    measure["census_minus_registered"] = measure["census_population"] - measure["registered_population"]
    measure["projection_minus_registered"] = measure["projection_population"] - measure["registered_population"]
    measure["census_minus_projection"] = measure["census_population"] - measure["projection_population"]
    write_csv(measure, "population_measure_comparison.csv")
    charts["population_measure_comparison"] = measure.to_dict("records")

    measure_gap = measure[
        [
            "year",
            "census_minus_registered",
            "projection_minus_registered",
            "census_minus_projection",
        ]
    ].copy()
    measure_gap["census_minus_registered_10k"] = (measure_gap["census_minus_registered"] / 10_000).round(1)
    measure_gap["projection_minus_registered_10k"] = (measure_gap["projection_minus_registered"] / 10_000).round(1)
    measure_gap["census_minus_projection_10k"] = (measure_gap["census_minus_projection"] / 10_000).round(1)
    write_csv(measure_gap, "population_measure_gap.csv")
    charts["population_measure_gap"] = measure_gap.to_dict("records")

    registration_jump = measure[["year", "registered_population", "projection_population"]].copy()
    registration_jump["annual_change"] = registration_jump["registered_population"].diff()
    registration_jump["annual_change_10k"] = (registration_jump["annual_change"] / 10_000).round(1)
    registration_jump["annual_growth_pct"] = (registration_jump["registered_population"].pct_change() * 100).round(3)
    registration_jump["registered_population_million"] = (registration_jump["registered_population"] / 1_000_000).round(3)
    registration_jump["projection_annual_change"] = registration_jump["projection_population"].diff()
    registration_jump["projection_annual_change_10k"] = (registration_jump["projection_annual_change"] / 10_000).round(1)
    registration_jump["is_2010"] = registration_jump["year"].eq(2010)
    registration_jump = registration_jump[registration_jump["year"].between(2001, 2024)]
    write_csv(registration_jump, "resident_registration_2010_jump.csv")
    charts["resident_registration_2010_jump"] = registration_jump.to_dict("records")

    centenarian_path = DATA / "resident_registration_national_age_DT_1B04006.csv"
    if centenarian_path.exists():
        centenarian_raw = pd.read_csv(centenarian_path)
        centenarian_raw["population"] = pd.to_numeric(centenarian_raw["population"], errors="coerce")
        centenarian = centenarian_raw[centenarian_raw["C2_NM"].isin(["계", "100세 이상"])].pivot_table(
            index="year",
            columns="C2_NM",
            values="population",
            aggfunc="first",
        ).reset_index()
        centenarian = centenarian.rename(columns={"계": "total_population", "100세 이상": "population_100_plus"})
        centenarian["population_100_plus"] = pd.to_numeric(centenarian["population_100_plus"], errors="coerce")
        centenarian["total_population"] = pd.to_numeric(centenarian["total_population"], errors="coerce")
        centenarian["share_100_plus_per_100k"] = (centenarian["population_100_plus"] / centenarian["total_population"] * 100_000).round(2)
        centenarian["annual_change_100_plus"] = centenarian["population_100_plus"].diff()
        centenarian = centenarian.sort_values("year")
        write_csv(centenarian, "resident_registration_centenarian_trend.csv")
        charts["resident_registration_centenarian_trend"] = centenarian.to_dict("records")

    sigungu_slope_map_path = DERIVED / "sigungu_population_trend_map_values.csv"
    if sigungu_slope_map_path.exists():
        sigungu_slope_map = pd.read_csv(sigungu_slope_map_path)
        write_csv(sigungu_slope_map, "sigungu_population_trend_map_values.csv")
        charts["sigungu_population_slope_map"] = sigungu_slope_map.to_dict("records")

    older_slope_map_path = DERIVED / "sigungu_older_population_trend_map_values.csv"
    if older_slope_map_path.exists():
        older_slope_map = pd.read_csv(older_slope_map_path)
        write_csv(older_slope_map, "sigungu_older_population_trend_map_values.csv")
        charts["sigungu_older_population_slope_map"] = older_slope_map.to_dict("records")

    working_age_slope_map_path = DERIVED / "sigungu_working_age_population_trend_map_values.csv"
    if working_age_slope_map_path.exists():
        working_age_slope_map = pd.read_csv(working_age_slope_map_path)
        write_csv(working_age_slope_map, "sigungu_working_age_population_trend_map_values.csv")
        charts["sigungu_working_age_population_slope_map"] = working_age_slope_map.to_dict("records")

    sigungu_population_path = DATA / "sigungu_population_2004_2024.csv"
    sigungu_slope_path = DERIVED / "sigungu_population_trend_slopes.csv"
    if sigungu_population_path.exists() and sigungu_slope_path.exists():
        sigungu_pop = pd.read_csv(sigungu_population_path)
        sigungu_pop["year"] = pd.to_numeric(sigungu_pop["year"], errors="coerce")
        sigungu_pop["population"] = pd.to_numeric(sigungu_pop["population"], errors="coerce")
        sigungu_pop["C1"] = sigungu_pop["C1"].astype(str).str.zfill(5)
        sigungu_pop["family_code"] = sigungu_pop["C1"].str[:4]
        sigungu_pop = sigungu_pop.dropna(subset=["year", "population"]).copy()

        bottom_rows = []
        for _, year_group in sigungu_pop.groupby("year"):
            year_group = year_group.copy()
            sibling_sum = (
                year_group[~year_group["C1"].str.endswith("0")]
                .groupby("family_code")["population"]
                .sum()
                .to_dict()
            )
            aggregate_with_child = year_group["C1"].str.endswith("0") & year_group.apply(
                lambda row: sibling_sum.get(row["family_code"], 0) > row["population"] * 0.5,
                axis=1,
            )
            zero_auxiliary = (~year_group["C1"].str.endswith("0")) & (year_group["population"] == 0)
            bottom_rows.append(year_group[~aggregate_with_child & ~zero_auxiliary].copy())
        bottom_pop = pd.concat(bottom_rows, ignore_index=True)

        slopes = pd.read_csv(sigungu_slope_path)
        slopes["C1"] = slopes["C1"].astype(str).str.zfill(5)
        current_bottom_codes = set(bottom_pop.loc[bottom_pop["year"] == bottom_pop["year"].max(), "C1"])
        top_growth_codes = set(
            slopes[slopes["C1"].isin(current_bottom_codes)]
            .sort_values("slope_people_per_year", ascending=False)
            .head(20)["C1"]
        )
        top_growth_hubs = (
            slopes[slopes["C1"].isin(top_growth_codes)]
            .sort_values("slope_people_per_year", ascending=False)
            .head(20)
        )
        write_csv(top_growth_hubs, "sigungu_population_top_growth_hubs.csv")

        concentration_rows = []
        rank_rows = []
        for year, year_group in bottom_pop.groupby("year"):
            year_group = year_group.sort_values("population", ascending=False).copy()
            year_group["rank"] = range(1, len(year_group) + 1)
            total_population = year_group["population"].sum()
            shares = year_group["population"] / total_population
            values = np.sort(year_group["population"].to_numpy())
            n_regions = len(values)
            gini = (
                (2 * np.arange(1, n_regions + 1).dot(values) / (n_regions * values.sum()))
                - ((n_regions + 1) / n_regions)
            )
            hhi = float((shares**2).sum() * 10000)
            concentration_rows.append(
                {
                    "year": int(year),
                    "municipality_count": int(n_regions),
                    "total_population": int(total_population),
                    "top_10_share_pct": round(year_group.head(10)["population"].sum() / total_population * 100, 3),
                    "top_20_share_pct": round(year_group.head(20)["population"].sum() / total_population * 100, 3),
                    "top_50_share_pct": round(year_group.head(50)["population"].sum() / total_population * 100, 3),
                    "capital_area_share_pct": round(
                        year_group[year_group["C1"].str[:2].isin(["11", "28", "41"])]["population"].sum()
                        / total_population
                        * 100,
                        3,
                    ),
                    "growth_hub_20_share_pct": round(
                        year_group[year_group["C1"].isin(top_growth_codes)]["population"].sum()
                        / total_population
                        * 100,
                        3,
                    ),
                    "gini": round(float(gini), 4),
                    "hhi": round(hhi, 3),
                    "effective_region_count": round(float(1 / (shares**2).sum()), 2),
                }
            )
            rank_rows.append(
                year_group.head(30)[
                    ["year", "rank", "C1", "C1_NM", "C1_NM_ENG", "population"]
                ].copy()
            )
        concentration = pd.DataFrame(concentration_rows).sort_values("year")
        concentration_indices = concentration[
            ["year", "gini", "hhi", "effective_region_count", "municipality_count"]
        ].copy()
        concentration_indices["gini_index_2004_100"] = (
            concentration_indices["gini"] / concentration_indices["gini"].iloc[0] * 100
        ).round(2)
        concentration_indices["hhi_index_2004_100"] = (
            concentration_indices["hhi"] / concentration_indices["hhi"].iloc[0] * 100
        ).round(2)
        concentration_indices["effective_region_count_index_2004_100"] = (
            concentration_indices["effective_region_count"]
            / concentration_indices["effective_region_count"].iloc[0]
            * 100
        ).round(2)
        ranks = pd.concat(rank_rows, ignore_index=True)
        write_csv(concentration, "sigungu_population_concentration.csv")
        write_csv(concentration_indices, "sigungu_population_concentration_indices.csv")
        write_csv(ranks, "sigungu_population_rank_snapshots.csv")
        charts["sigungu_population_concentration"] = concentration.to_dict("records")
        charts["sigungu_population_concentration_indices"] = concentration_indices.to_dict("records")

    cohort = pd.read_csv(DATA / "yeonggwang_birth_cohort_summary.csv")
    write_csv(cohort, "yeonggwang_birth_cohort_summary.csv")
    charts["yeonggwang_cohort"] = cohort.to_dict("records")

    birth_incentive_path = DERIVED / "birth_incentive_region_panel_cbr_retention.csv"
    if birth_incentive_path.exists():
        birth_incentive = pd.read_csv(birth_incentive_path)
        write_csv(birth_incentive, "birth_incentive_region_panel_cbr_retention.csv")
        charts["birth_incentive_region_retention"] = birth_incentive.to_dict("records")

    birth_incentive_summary_path = DERIVED / "birth_incentive_region_cohort_summary.csv"
    if birth_incentive_summary_path.exists():
        birth_incentive_summary = pd.read_csv(birth_incentive_summary_path)
        write_csv(birth_incentive_summary, "birth_incentive_region_cohort_summary.csv")
        charts["birth_incentive_region_summary"] = birth_incentive_summary.to_dict("records")

    fertility = pd.DataFrame(
        {
            "year": [2000, 2005, 2010, 2015, 2020, 2021, 2022, 2023, 2024],
            "yeonggwang": [1.832, 1.375, 1.538, 1.434, 2.455, 1.869, 1.803, 1.653, 1.701],
            "national": [1.480, 1.085, 1.226, 1.239, 0.837, 0.808, 0.778, 0.721, 0.750],
        }
    )
    write_csv(fertility, "fertility_comparison.csv")
    charts["fertility_comparison"] = fertility.to_dict("records")

    wb_tfr_path = DATA / "worldbank_tfr_selected_countries.csv"
    if wb_tfr_path.exists():
        wb_tfr = pd.read_csv(wb_tfr_path)
        wb_tfr["year"] = pd.to_numeric(wb_tfr["year"], errors="coerce")
        wb_tfr["total_fertility_rate"] = pd.to_numeric(wb_tfr["total_fertility_rate"], errors="coerce")
        country_meta = {
            "KOR": ("한국", "아시아"),
            "JPN": ("일본", "아시아"),
            "SGP": ("싱가포르", "아시아"),
            "FRA": ("프랑스", "유럽"),
            "SWE": ("스웨덴", "유럽"),
            "DEU": ("독일", "유럽"),
            "ITA": ("이탈리아", "유럽"),
            "ESP": ("스페인", "유럽"),
            "GBR": ("영국", "유럽"),
        }
        tfr_rows = wb_tfr[wb_tfr["country_code"].isin(country_meta)].copy()
        tfr_rows = tfr_rows.dropna(subset=["year", "total_fertility_rate"])
        tfr_rows["year"] = tfr_rows["year"].astype(int)
        tfr_rows["country_display"] = tfr_rows["country_code"].map(lambda code: country_meta[code][0])
        tfr_rows["region_group"] = tfr_rows["country_code"].map(lambda code: country_meta[code][1])
        taiwan_values = {
            2000: 1.680,
            2001: 1.400,
            2002: 1.340,
            2003: 1.235,
            2004: 1.180,
            2005: 1.115,
            2006: 1.115,
            2007: 1.100,
            2008: 1.050,
            2009: 1.030,
            2010: 0.895,
            2011: 1.065,
            2012: 1.270,
            2013: 1.065,
            2014: 1.165,
            2015: 1.175,
            2016: 1.170,
            2017: 1.125,
            2018: 1.060,
            2019: 1.050,
            2020: 0.990,
            2021: 0.975,
            2022: 0.870,
            2023: 0.865,
            2024: 0.885,
        }
        taiwan = pd.DataFrame(
            {
                "country_code": "TWN",
                "country": "Taiwan",
                "year": list(taiwan_values.keys()),
                "total_fertility_rate": list(taiwan_values.values()),
                "country_display": "대만",
                "region_group": "아시아",
            }
        )
        international_tfr = pd.concat(
            [
                tfr_rows[
                    [
                        "country_code",
                        "country",
                        "year",
                        "total_fertility_rate",
                        "country_display",
                        "region_group",
                    ]
                ],
                taiwan,
            ],
            ignore_index=True,
        )
        international_tfr = international_tfr[international_tfr["year"].between(2000, 2024)].copy()
        international_tfr = international_tfr.sort_values(["region_group", "country_display", "year"])
        write_csv(international_tfr, "international_tfr_trends.csv")
        charts["international_tfr_asia"] = international_tfr[international_tfr["region_group"] == "아시아"].to_dict("records")
        charts["international_tfr_europe"] = international_tfr[international_tfr["region_group"] == "유럽"].to_dict("records")

        latest_tfr = (
            international_tfr.sort_values("year")
            .dropna(subset=["total_fertility_rate"])
            .groupby("country_code", as_index=False)
            .tail(1)[["country_code", "country_display", "region_group", "year", "total_fertility_rate"]]
            .rename(columns={"year": "tfr_year"})
        )
        nonmarital_path = DATA / "owid_share_births_outside_marriage.csv"
        nonmarital_latest = pd.DataFrame()
        if nonmarital_path.exists():
            nonmarital = pd.read_csv(nonmarital_path)
            nonmarital = nonmarital.rename(
                columns={
                    "Code": "country_code",
                    "Year": "nonmarital_year",
                    "Share of births outside marriage": "nonmarital_birth_share_pct",
                }
            )
            nonmarital["nonmarital_year"] = pd.to_numeric(nonmarital["nonmarital_year"], errors="coerce")
            nonmarital["nonmarital_birth_share_pct"] = pd.to_numeric(
                nonmarital["nonmarital_birth_share_pct"], errors="coerce"
            )
            nonmarital_latest = (
                nonmarital[nonmarital["country_code"].isin(["KOR", "JPN", "FRA", "SWE", "DEU", "ITA", "ESP", "GBR"])]
                .dropna(subset=["nonmarital_birth_share_pct"])
                .sort_values("nonmarital_year")
                .groupby("country_code", as_index=False)
                .tail(1)[["country_code", "nonmarital_year", "nonmarital_birth_share_pct"]]
            )
        family_compare = latest_tfr[latest_tfr["country_code"].isin(["KOR", "JPN", "FRA", "SWE", "DEU", "ITA", "ESP", "GBR"])].copy()
        if not nonmarital_latest.empty:
            family_compare = family_compare.merge(nonmarital_latest, on="country_code", how="left")
        foreign_path = DATA / "eurostat_foreign_born_mother_births_2023.csv"
        if foreign_path.exists():
            foreign = pd.read_csv(foreign_path)
            foreign_code_map = {"DE": "DEU", "ES": "ESP", "FR": "FRA", "IT": "ITA", "SE": "SWE"}
            foreign["country_code"] = foreign["geo"].map(foreign_code_map)
            foreign = foreign.dropna(subset=["country_code"])
            foreign = foreign[
                ["country_code", "year", "foreign_born_mother_births", "total_births", "foreign_born_mother_share_pct"]
            ].rename(columns={"year": "foreign_born_mother_year"})
            family_compare = family_compare.merge(foreign, on="country_code", how="left")
        family_compare = family_compare.sort_values(["region_group", "total_fertility_rate"], ascending=[True, False])
        write_csv(family_compare, "fertility_family_structure_comparison.csv")
        charts["fertility_family_structure_comparison"] = family_compare.to_dict("records")

    fertility_age_path = DATA / "fertility_by_mother_age_DT_1B81A21.csv"
    if fertility_age_path.exists():
        fertility_age = pd.read_csv(fertility_age_path)
        fertility_age = fertility_age[fertility_age["C1_NM"] == "전국"].copy()
        fertility_age["DT"] = pd.to_numeric(fertility_age["DT"], errors="coerce")
        fertility_age = fertility_age.pivot_table(index="PRD_DE", columns="ITM_NM", values="DT", aggfunc="first").reset_index()
        fertility_age = fertility_age.rename(
            columns={
                "PRD_DE": "year",
                "합계출산율": "total_fertility_rate",
                "25-29세": "asfr_25_29",
                "30-34세": "asfr_30_34",
                "35-39세": "asfr_35_39",
                "40-44세": "asfr_40_44",
            }
        )
        cols = ["year", "total_fertility_rate", "asfr_25_29", "asfr_30_34", "asfr_35_39", "asfr_40_44"]
        fertility_age = fertility_age[[c for c in cols if c in fertility_age.columns]].sort_values("year")
        write_csv(fertility_age, "fertility_age_pattern.csv")
        charts["fertility_age_pattern"] = fertility_age.to_dict("records")

    birth_age_path = DATA / "mean_birth_age_DT_1B81A20.csv"
    if birth_age_path.exists():
        birth_age = pd.read_csv(birth_age_path)
        birth_age = birth_age[birth_age["C1_NM"] == "전국"].copy()
        birth_age["DT"] = pd.to_numeric(birth_age["DT"], errors="coerce")
        birth_age = birth_age.pivot_table(index="PRD_DE", columns="ITM_NM", values="DT", aggfunc="first").reset_index()
        birth_age = birth_age.rename(
            columns={
                "PRD_DE": "year",
                "모의 평균 출산 연령": "mean_birth_age",
                "첫째 아": "first_child_age",
                "둘째 아": "second_child_age",
            }
        )
        birth_age = birth_age[["year", "mean_birth_age", "first_child_age", "second_child_age"]].sort_values("year")
        write_csv(birth_age, "mean_birth_age_order.csv")
        charts["mean_birth_age_order"] = birth_age.to_dict("records")

    vital_path = DATA / "vital_rates_DT_1B8000H.csv"
    if vital_path.exists():
        vital = pd.read_csv(vital_path)
        vital = vital[vital["C1_NM"] == "전국"].copy()
        vital["DT"] = pd.to_numeric(vital["DT"], errors="coerce")
        vital = vital.pivot_table(index="PRD_DE", columns="ITM_NM", values="DT", aggfunc="first").reset_index()
        vital = vital.rename(
            columns={
                "PRD_DE": "year",
                "출생건수 (명)": "births",
                "사망건수 (명)": "deaths",
                "혼인건수 (건)": "marriages",
                "이혼건수 (건)": "divorces",
                "자연증가건수 (명)": "natural_increase",
            }
        )
        vital_cols = ["year", "births", "deaths", "natural_increase", "marriages", "divorces"]
        vital = vital[[c for c in vital_cols if c in vital.columns]].sort_values("year")
        write_csv(vital, "vital_events_policy.csv")
        charts["vital_events_policy"] = vital.to_dict("records")

    marriage_attitude = pd.DataFrame(
        [
            {"year": 2010, "gender": "미혼 남성", "marriage_positive_pct": 62.6},
            {"year": 2010, "gender": "미혼 여성", "marriage_positive_pct": 46.8},
            {"year": 2024, "gender": "미혼 남성", "marriage_positive_pct": 41.6},
            {"year": 2024, "gender": "미혼 여성", "marriage_positive_pct": 26.0},
        ]
    )
    marriage_attitude["gap_from_2010_pctp"] = marriage_attitude.apply(
        lambda row: round(
            row["marriage_positive_pct"]
            - marriage_attitude[
                (marriage_attitude["year"] == 2010)
                & (marriage_attitude["gender"] == row["gender"])
            ]["marriage_positive_pct"].iloc[0],
            1,
        ),
        axis=1,
    )
    write_csv(marriage_attitude, "marriage_attitude_unmarried_gender.csv")
    charts["marriage_attitude_unmarried_gender"] = marriage_attitude.to_dict("records")

    family_norms = pd.DataFrame(
        [
            {"year": 2010, "indicator": "결혼해야 한다", "positive_pct": 64.7},
            {"year": 2010, "indicator": "결혼하지 않아도 함께 살 수 있다", "positive_pct": 40.5},
            {"year": 2010, "indicator": "결혼하지 않고도 자녀를 가질 수 있다", "positive_pct": 20.6},
            {"year": 2024, "indicator": "결혼해야 한다", "positive_pct": 52.5},
            {"year": 2024, "indicator": "결혼하지 않아도 함께 살 수 있다", "positive_pct": 67.4},
            {"year": 2024, "indicator": "결혼하지 않고도 자녀를 가질 수 있다", "positive_pct": 37.2},
        ]
    )
    family_norms["change_from_2010_pctp"] = family_norms.apply(
        lambda row: round(
            row["positive_pct"]
            - family_norms[
                (family_norms["year"] == 2010)
                & (family_norms["indicator"] == row["indicator"])
            ]["positive_pct"].iloc[0],
            1,
        ),
        axis=1,
    )
    write_csv(family_norms, "family_norms_culture_shift.csv")
    charts["family_norms_culture_shift"] = family_norms.to_dict("records")

    divorce_rate_path = DATA / "divorce_rate_by_age_DT_1B85009.csv"
    if divorce_rate_path.exists():
        divorce_rate = pd.read_csv(divorce_rate_path)
        divorce_rate = divorce_rate[divorce_rate["C1_NM"] == "계"].copy()
        divorce_rate["year"] = pd.to_numeric(divorce_rate["PRD_DE"], errors="coerce").astype("Int64")
        divorce_rate["divorce_rate_per_1000"] = pd.to_numeric(divorce_rate["DT"], errors="coerce")
        divorce_rate["sex"] = divorce_rate["ITM_NM"].map(
            {
                "남편(해당연령 천명당 건)": "남편",
                "아내(해당연령 천명당 건)": "아내",
            }
        )
        divorce_rate["decade"] = divorce_rate["C2_NM"].map(
            {
                "30 - 34세": "30대",
                "35 - 39세": "30대",
                "40 - 44세": "40대",
                "45 - 49세": "40대",
            }
        )
        divorce_rate = divorce_rate.dropna(subset=["sex", "decade", "year", "divorce_rate_per_1000"])
        divorce_age_trend = (
            divorce_rate.groupby(["year", "sex", "decade"], as_index=False)["divorce_rate_per_1000"]
            .mean()
            .sort_values(["year", "decade", "sex"])
        )
        divorce_age_trend["divorce_rate_per_1000"] = divorce_age_trend["divorce_rate_per_1000"].round(2)
        write_csv(divorce_age_trend, "divorce_rate_30s_40s_trend.csv")
        charts["divorce_rate_30s_40s_trend"] = divorce_age_trend.to_dict("records")

    divorce_acceptance_trend = pd.DataFrame(
        [
            {"year": 2014, "positive_pct": 12.0},
            {"year": 2016, "positive_pct": 14.0},
            {"year": 2018, "positive_pct": 16.7},
            {"year": 2020, "positive_pct": 16.8},
            {"year": 2022, "positive_pct": 18.7},
            {"year": 2024, "positive_pct": 20.5},
        ]
    )
    write_csv(divorce_acceptance_trend, "divorce_acceptance_trend.csv")
    charts["divorce_acceptance_trend"] = divorce_acceptance_trend.to_dict("records")

    divorce_acceptance_profile = pd.DataFrame(
        [
            {"category": "전체", "negative_pct": 26.6, "neutral_pct": 48.2, "positive_pct": 20.5, "unknown_pct": 4.6},
            {"category": "남자", "negative_pct": 30.2, "neutral_pct": 46.7, "positive_pct": 17.9, "unknown_pct": 5.2},
            {"category": "여자", "negative_pct": 23.1, "neutral_pct": 49.7, "positive_pct": 23.1, "unknown_pct": 4.1},
            {"category": "미혼", "negative_pct": 13.6, "neutral_pct": 51.5, "positive_pct": 26.9, "unknown_pct": 8.0},
            {"category": "미혼 남자", "negative_pct": 17.9, "neutral_pct": 49.9, "positive_pct": 23.3, "unknown_pct": 8.8},
            {"category": "미혼 여자", "negative_pct": 7.9, "neutral_pct": 53.5, "positive_pct": 31.6, "unknown_pct": 7.0},
            {"category": "20-29세", "negative_pct": 13.1, "neutral_pct": 53.0, "positive_pct": 27.5, "unknown_pct": 6.4},
            {"category": "30-39세", "negative_pct": 18.2, "neutral_pct": 53.8, "positive_pct": 23.3, "unknown_pct": 4.7},
            {"category": "40-49세", "negative_pct": 20.2, "neutral_pct": 55.5, "positive_pct": 21.3, "unknown_pct": 3.1},
            {"category": "60세 이상", "negative_pct": 45.3, "neutral_pct": 35.7, "positive_pct": 15.3, "unknown_pct": 3.8},
        ]
    )
    divorce_acceptance_profile["acceptance_pct"] = (
        divorce_acceptance_profile["neutral_pct"] + divorce_acceptance_profile["positive_pct"]
    ).round(1)
    write_csv(divorce_acceptance_profile, "divorce_acceptance_profile_2024.csv")
    charts["divorce_acceptance_profile_2024"] = divorce_acceptance_profile.to_dict("records")

    youth_marriage_profile = pd.DataFrame(
        [
            {"axis": "청년 전체", "category": "19-34세 전체", "positive_pct": 36.4, "change_from_2012_pctp": -20.1},
            {"axis": "성별", "category": "남자", "positive_pct": 43.8, "change_from_2012_pctp": -22.3},
            {"axis": "성별", "category": "여자", "positive_pct": 28.0, "change_from_2012_pctp": -18.9},
            {"axis": "연령대", "category": "19-24세", "positive_pct": 34.0, "change_from_2012_pctp": None},
            {"axis": "연령대", "category": "25-29세", "positive_pct": 36.1, "change_from_2012_pctp": -23.4},
            {"axis": "연령대", "category": "30-34세", "positive_pct": 39.2, "change_from_2012_pctp": None},
        ]
    )
    write_csv(youth_marriage_profile, "marriage_attitude_youth_profile_2022.csv")
    charts["marriage_attitude_youth_profile_2022"] = youth_marriage_profile.to_dict("records")

    young_women_25_29 = pd.DataFrame(
        [
            {"period": "2024.3", "indicator": "결혼 의향", "positive_pct": 56.6},
            {"period": "2025.3", "indicator": "결혼 의향", "positive_pct": 64.0},
            {"period": "2024.3", "indicator": "자녀 필요성", "positive_pct": 34.4},
            {"period": "2025.3", "indicator": "자녀 필요성", "positive_pct": 48.7},
        ]
    )
    write_csv(young_women_25_29, "young_women_25_29_recent_attitudes.csv")
    charts["young_women_25_29_recent_attitudes"] = young_women_25_29.to_dict("records")

    tfr_gender_conflict = pd.DataFrame({"year": list(range(2013, 2025))})
    if fertility_age_path.exists():
        tfr_source = pd.read_csv(fertility_age_path)
        tfr_source = tfr_source[(tfr_source["C1_NM"] == "전국") & (tfr_source["ITM_NM"] == "합계출산율")].copy()
        tfr_source["year"] = pd.to_numeric(tfr_source["PRD_DE"], errors="coerce")
        tfr_source["tfr"] = pd.to_numeric(tfr_source["DT"], errors="coerce")
        tfr_gender_conflict = tfr_gender_conflict.merge(tfr_source[["year", "tfr"]], on="year", how="left")
    conflict_points = pd.DataFrame(
        [
            {"year": 2013, "gender_conflict_very_serious_pct": 7.2},
            {"year": 2018, "gender_conflict_very_serious_pct": 11.5},
            {"year": 2019, "gender_conflict_very_serious_pct": 11.7},
            {"year": 2020, "gender_conflict_very_serious_pct": 8.7},
            {"year": 2021, "gender_conflict_very_serious_pct": 9.9},
            {"year": 2022, "gender_conflict_very_serious_pct": 6.1},
            {"year": 2023, "gender_conflict_very_serious_pct": 4.9},
        ]
    )
    tfr_gender_conflict = tfr_gender_conflict.merge(conflict_points, on="year", how="left")
    tfr_gender_conflict["late_2010s_drop_window"] = tfr_gender_conflict["year"].between(2016, 2019)
    write_csv(tfr_gender_conflict, "tfr_gender_conflict_timeline.csv")
    charts["tfr_gender_conflict_timeline"] = tfr_gender_conflict.to_dict("records")

    if fertility_age_path.exists() and vital_path.exists():
        fertility_raw = pd.read_csv(fertility_age_path)
        fertility_raw = fertility_raw[fertility_raw["C1_NM"] == "전국"].copy()
        fertility_raw["year"] = pd.to_numeric(fertility_raw["PRD_DE"], errors="coerce")
        fertility_raw["DT"] = pd.to_numeric(fertility_raw["DT"], errors="coerce")

        tfr = fertility_raw[fertility_raw["ITM_NM"] == "합계출산율"][["year", "DT"]].rename(
            columns={"DT": "total_fertility_rate"}
        )

        asfr_names = {
            "15-19세": "asfr_15_19",
            "20-24세": "asfr_20_24",
            "25-29세": "asfr_25_29",
            "30-34세": "asfr_30_34",
            "35-39세": "asfr_35_39",
            "40-44세": "asfr_40_44",
        }
        fertility_asfr = (
            fertility_raw[fertility_raw["ITM_NM"].isin(asfr_names)]
            .pivot_table(index="year", columns="ITM_NM", values="DT", aggfunc="first")
            .reset_index()
            .rename(columns=asfr_names)
        )
        asfr_cols = ["year"] + [col for col in asfr_names.values() if col in fertility_asfr.columns]
        fertility_asfr = fertility_asfr[asfr_cols].sort_values("year")
        write_csv(fertility_asfr, "fertility_asfr_shift.csv")
        charts["fertility_asfr_shift"] = fertility_asfr.to_dict("records")

        vital_rates = pd.read_csv(vital_path)
        vital_rates = vital_rates[vital_rates["C1_NM"] == "전국"].copy()
        vital_rates["year"] = pd.to_numeric(vital_rates["PRD_DE"], errors="coerce")
        vital_rates["DT"] = pd.to_numeric(vital_rates["DT"], errors="coerce")
        vital_rates = (
            vital_rates[vital_rates["ITM_NM"].isin(["출생건수 (명)", "조출생률 (천명당)"])]
            .pivot_table(index="year", columns="ITM_NM", values="DT", aggfunc="first")
            .reset_index()
            .rename(columns={"출생건수 (명)": "births", "조출생률 (천명당)": "crude_birth_rate"})
        )

        female_pop = pyramid_raw[
            (pyramid_raw["C1"].astype(str).eq("1"))
            & (pyramid_raw["C2"].astype(str).eq("2"))
            & pyramid_raw["C3_NM"].astype(str).str.fullmatch(r"\d+세")
        ].copy()
        female_pop["age"] = female_pop["C3_NM"].astype(str).str.extract(r"(\d+)").astype(float)
        female_15_49 = (
            female_pop[female_pop["age"].between(15, 49)]
            .groupby("PRD_DE", as_index=False)["DT"]
            .sum()
            .rename(columns={"PRD_DE": "year", "DT": "female_15_49_population"})
        )
        female_15_49["year"] = pd.to_numeric(female_15_49["year"], errors="coerce")

        fertility_summary = (
            tfr.merge(vital_rates, on="year", how="inner")
            .merge(female_15_49, on="year", how="inner")
            .sort_values("year")
        )
        fertility_summary["general_fertility_rate"] = (
            fertility_summary["births"] / fertility_summary["female_15_49_population"] * 1000
        )
        fertility_summary = fertility_summary[fertility_summary["year"].between(2000, 2024)].copy()
        if not fertility_summary.empty:
            base = fertility_summary.iloc[0]
            fertility_summary["tfr_index"] = fertility_summary["total_fertility_rate"] / base["total_fertility_rate"] * 100
            fertility_summary["cbr_index"] = fertility_summary["crude_birth_rate"] / base["crude_birth_rate"] * 100
            fertility_summary["gfr_index"] = fertility_summary["general_fertility_rate"] / base["general_fertility_rate"] * 100
        fertility_summary = fertility_summary[
            [
                "year",
                "births",
                "female_15_49_population",
                "total_fertility_rate",
                "crude_birth_rate",
                "general_fertility_rate",
                "tfr_index",
                "cbr_index",
                "gfr_index",
            ]
        ].round(3)
        write_csv(fertility_summary, "fertility_measure_summary.csv")
        charts["fertility_measure_summary"] = fertility_summary.to_dict("records")

        cohort_midpoints = {"20-24세": 22, "25-29세": 27, "30-34세": 32, "35-39세": 37}
        cohort_parts = []
        for age_group, midpoint in cohort_midpoints.items():
            part = fertility_raw[fertility_raw["ITM_NM"] == age_group][["year", "DT"]].copy()
            part["cohort_birth_year"] = part["year"] - midpoint
            part["age_group"] = age_group
            part["fertility_contribution"] = part["DT"] / 1000 * 5
            cohort_parts.append(part)
        cohort_long = pd.concat(cohort_parts, ignore_index=True)
        cohort_fertility = (
            cohort_long.groupby("cohort_birth_year", as_index=False)
            .agg(
                cumulative_fertility_20_39=("fertility_contribution", "sum"),
                observed_age_groups=("age_group", "nunique"),
                first_observed_year=("year", "min"),
                last_observed_year=("year", "max"),
            )
            .query("observed_age_groups == 4")
            .sort_values("cohort_birth_year")
        )
        cohort_fertility = cohort_fertility[
            cohort_fertility["cohort_birth_year"].between(1978, 1987)
        ].round(3)
        write_csv(cohort_fertility, "cohort_fertility_by_birth_year.csv")
        charts["cohort_fertility_by_birth_year"] = cohort_fertility.to_dict("records")

    sig = pd.read_csv(DATA / "sigungu_aging_2024.csv")
    sig_top = sig.sort_values("aging_rate", ascending=False).head(20)
    write_csv(sig_top, "sigungu_aging_top.csv")
    charts["sigungu_aging_top"] = sig_top.to_dict("records")

    bins = [0, 20, 30, 40, 100]
    labels = ["20% 미만", "20-30%", "30-40%", "40% 이상"]
    sig_dist = sig.copy()
    sig_dist["aging_class"] = pd.cut(sig_dist["aging_rate"], bins=bins, labels=labels, right=False)
    sig_dist = sig_dist.groupby("aging_class", observed=False).agg(
        sigungu_count=("C1", "count"),
        total_population=("total_population", "sum"),
        older_population=("older_population", "sum"),
    ).reset_index()
    sig_dist["older_population_share"] = (sig_dist["older_population"] / sig_dist["total_population"] * 100).round(2)
    write_csv(sig_dist, "sigungu_aging_distribution.csv")
    charts["sigungu_aging_distribution"] = sig_dist.to_dict("records")

    migration_path = DATA / "domestic_migration_age_DT_1B26001_A03.csv"
    if migration_path.exists():
        migration_raw = pd.read_csv(
            migration_path,
            usecols=["PRD_DE", "C1", "C1_NM", "C2", "C2_NM", "ITM_ID", "DT"],
            dtype={"C1": str, "C2": str, "ITM_ID": str},
        )
        migration_raw["year"] = pd.to_numeric(migration_raw["PRD_DE"], errors="coerce")
        migration_raw["net_migration"] = pd.to_numeric(migration_raw["DT"], errors="coerce")
        migration_raw["C1"] = migration_raw["C1"].astype(str)
        migration_raw["C2"] = migration_raw["C2"].astype(str).str.zfill(3)

        migration_net = migration_raw[
            (migration_raw["ITM_ID"] == "T25")
            & migration_raw["C1"].str.fullmatch(r"\d{2}")
            & (migration_raw["C1"] != "00")
        ].copy()

        sido_total = migration_net[migration_net["C2"] == "000"].copy()
        latest_year = int(sido_total["year"].max())
        recent_start_year = latest_year - 9
        recent_avg_col = f"avg_net_migration_{recent_start_year}_{latest_year}"
        latest_col = f"net_migration_{latest_year}"
        recent_average = (
            sido_total[sido_total["year"].between(recent_start_year, latest_year)]
            .groupby("C1", as_index=False)["net_migration"]
            .mean()
            .rename(columns={"net_migration": recent_avg_col})
        )
        latest = (
            sido_total[sido_total["year"] == latest_year][["C1", "net_migration"]]
            .rename(columns={"net_migration": latest_col})
        )
        sido_total = (
            sido_total.merge(recent_average, on="C1", how="left")
            .merge(latest, on="C1", how="left")
            .rename(columns={"C1_NM": "region"})
        )
        sido_total["avg_net_migration_recent"] = sido_total[recent_avg_col]
        sido_total["latest_net_migration"] = sido_total[latest_col]
        sido_total["recent_start_year"] = recent_start_year
        sido_total["latest_year"] = latest_year
        sido_total = sido_total[
            [
                "year",
                "C1",
                "region",
                "net_migration",
                "avg_net_migration_recent",
                "latest_net_migration",
                "recent_start_year",
                "latest_year",
                recent_avg_col,
                latest_col,
            ]
        ].sort_values(["C1", "year"])
        write_csv(sido_total, "sido_net_migration_total.csv")
        charts["sido_net_migration_panel"] = sido_total.to_dict("records")

        age_band_map = {
            "020": "0-14세",
            "050": "0-14세",
            "070": "0-14세",
            "100": "15-19세",
            "120": "20-24세",
            "130": "25-29세",
            "150": "30-34세",
            "160": "35-44세",
            "180": "35-44세",
            "190": "45-64세",
            "210": "45-64세",
            "230": "45-64세",
            "260": "45-64세",
            "280": "65세 이상",
            "310": "65세 이상",
            "330": "65세 이상",
            "340": "65세 이상",
        }
        age_long = migration_net[migration_net["C2"] != "000"].copy()
        age_long["age_band"] = age_long["C2"].map(age_band_map)
        age_long = age_long.dropna(subset=["age_band"])
        age_band_year = (
            age_long.groupby(["C1", "C1_NM", "year", "age_band"], as_index=False)["net_migration"]
            .sum()
            .rename(columns={"C1_NM": "region"})
        )
        write_csv(age_band_year, "sido_net_migration_age_by_year.csv")

        age_recent = (
            age_band_year[age_band_year["year"].between(recent_start_year, latest_year)]
            .groupby(["C1", "region", "age_band"], as_index=False)["net_migration"]
            .mean()
            .rename(columns={"net_migration": "avg_net_migration_recent"})
        )
        age_recent["recent_start_year"] = recent_start_year
        age_recent["latest_year"] = latest_year
        write_csv(age_recent, "sido_net_migration_age_contribution_long.csv")
        age_wide = (
            age_recent.pivot_table(
                index=["C1", "region"],
                columns="age_band",
                values="avg_net_migration_recent",
                aggfunc="first",
            )
            .reset_index()
            .fillna(0)
        )
        age_order = ["0-14세", "15-19세", "20-24세", "25-29세", "30-34세", "35-44세", "45-64세", "65세 이상"]
        for age_band in age_order:
            if age_band not in age_wide.columns:
                age_wide[age_band] = 0
        age_wide["avg_total_net_migration_recent"] = age_wide[age_order].sum(axis=1)
        age_wide["avg_total_net_migration_2016_2025"] = age_wide["avg_total_net_migration_recent"]
        age_wide["recent_start_year"] = recent_start_year
        age_wide["latest_year"] = latest_year
        age_wide["dominant_age_band"] = age_wide[age_order].abs().idxmax(axis=1)
        age_wide["dominant_age_contribution"] = age_wide.apply(
            lambda row: row[row["dominant_age_band"]],
            axis=1,
        )
        age_wide["absolute_component_sum"] = age_wide[age_order].abs().sum(axis=1)
        age_wide["dominant_abs_share_pct"] = (
            age_wide["dominant_age_contribution"].abs()
            / age_wide["absolute_component_sum"].where(age_wide["absolute_component_sum"] != 0)
            * 100
        ).round(1)
        for column in age_order + [
            "avg_total_net_migration_recent",
            "avg_total_net_migration_2016_2025",
            "dominant_age_contribution",
            "absolute_component_sum",
        ]:
            age_wide[column] = age_wide[column].round(1)
        age_wide = age_wide.sort_values("avg_total_net_migration_recent")
        write_csv(age_wide, "sido_net_migration_age_contribution.csv")
        charts["sido_net_migration_age_contribution"] = age_wide.to_dict("records")

        model_summary = age_wide[
            [
                "C1",
                "region",
                "avg_total_net_migration_recent",
                "dominant_age_band",
                "dominant_age_contribution",
                "dominant_abs_share_pct",
                "recent_start_year",
                "latest_year",
            ]
        ].copy()
        model_summary["model"] = "M_rt = sum_a m_rta"
        model_summary["interpretation"] = model_summary.apply(
            lambda row: f"{row['dominant_age_band']} 순이동이 최근 10년 평균 총순이동을 가장 크게 설명",
            axis=1,
        )
        write_csv(model_summary, "sido_net_migration_age_model_summary.csv")

        migration = migration_net[
            (migration_net["C1_NM"].isin(["서울특별시", "경기도"]))
            & (migration_net["C2_NM"].isin(["20 - 24세", "25 - 29세", "30 - 34세", "35 - 39세"]))
        ].copy()
        migration["age_group"] = migration["C2_NM"].map({"20 - 24세": "20s", "25 - 29세": "20s", "30 - 34세": "30s", "35 - 39세": "30s"})
        migration = migration.groupby(["year", "C1_NM", "age_group"], as_index=False)["net_migration"].sum()
        migration["series"] = migration["C1_NM"] + "_" + migration["age_group"]
        migration = migration.pivot_table(index="year", columns="series", values="net_migration", aggfunc="first").reset_index()
        migration = migration.rename(columns={"경기도_20s": "gyeonggi_20s", "경기도_30s": "gyeonggi_30s", "서울특별시_20s": "seoul_20s", "서울특별시_30s": "seoul_30s"})
        migration = migration.sort_values("year")
        write_csv(migration, "young_migration_policy.csv")
        charts["young_migration_policy"] = migration.to_dict("records")

    enara = pd.read_csv(DATA / "enara_population_policy_indicator.csv")
    youth = enara[enara["항목명"] == "생산가능인구"].copy()
    youth = youth.rename(columns={"주기": "year", "값": "youth_working_age_population"})
    youth = youth[["year", "youth_working_age_population"]]
    write_csv(youth, "youth_population_enara.csv")
    charts["youth_population_enara"] = youth.to_dict("records")

    youth_context = enara[enara["항목명"].isin(["생산가능인구", "경제활동인구", "취업자"])].copy()
    youth_context["year"] = pd.to_numeric(youth_context["주기"], errors="coerce")
    youth_context["value"] = pd.to_numeric(youth_context["값"], errors="coerce")
    youth_context = youth_context.pivot_table(index="year", columns="항목명", values="value", aggfunc="first").reset_index()
    youth_context = youth_context.rename(
        columns={
            "생산가능인구": "working_age_population",
            "경제활동인구": "economically_active_population",
            "취업자": "employed_population",
        }
    )
    for source_col, target_col in [
        ("working_age_population", "working_age_population_index"),
        ("economically_active_population", "economically_active_population_index"),
        ("employed_population", "employed_population_index"),
    ]:
        if source_col in youth_context.columns and not youth_context[source_col].dropna().empty:
            base = youth_context.loc[youth_context[source_col].notna(), source_col].iloc[0]
            youth_context[target_col] = youth_context[source_col] / base * 100
    youth_context = youth_context[[
        "year",
        "working_age_population_index",
        "economically_active_population_index",
        "employed_population_index",
    ]].dropna(how="all", subset=[
        "working_age_population_index",
        "economically_active_population_index",
        "employed_population_index",
    ])
    write_csv(youth_context, "youth_employment_context.csv")
    charts["youth_employment_context"] = youth_context.to_dict("records")

    leave_path = DATA / "enara_150401_raw.html"
    if leave_path.exists():
        leave_raw = pd.read_html(str(leave_path))[0]
        leave_raw.iloc[:, 0] = leave_raw.iloc[:, 0].astype(str).str.replace("\xa0", " ", regex=False)
        leave_raw.iloc[:, 1] = leave_raw.iloc[:, 1].astype(str).str.replace("\xa0", " ", regex=False)
        leave_records = []
        for row_index, row in leave_raw.iterrows():
            for column in leave_raw.columns[2:]:
                leave_records.append(
                    {
                        "year": int(column),
                        "row": int(row_index),
                        "category": row.iloc[0],
                        "group": row.iloc[1],
                        "value": pd.to_numeric(row[column], errors="coerce"),
                    }
                )
        leave_long = pd.DataFrame(leave_records)
        write_csv(leave_long, "enara_150401_long.csv")
        charts["enara_150401_long"] = leave_long.to_dict("records")

        leave_wide = leave_long.pivot_table(index="year", columns="row", values="value", aggfunc="first").reset_index()
        leave_summary = pd.DataFrame(
            {
                "year": leave_wide["year"],
                "maternity_leave_users": leave_wide[0],
                "maternity_leave_amount_million_krw": leave_wide[1],
                "parental_leave_total_users": leave_wide[2],
                "female_parental_leave_users": leave_wide[3],
                "male_parental_leave_users": leave_wide[4],
                "parental_leave_amount_million_krw": leave_wide[5],
                "female_parental_leave_amount_million_krw": leave_wide[6],
                "male_parental_leave_amount_million_krw": leave_wide[7],
            }
        ).sort_values("year")
        leave_summary["male_parental_leave_share_pct"] = (
            leave_summary["male_parental_leave_users"] / leave_summary["parental_leave_total_users"] * 100
        ).round(2)
        leave_summary["maternity_leave_per_user_million_krw"] = (
            leave_summary["maternity_leave_amount_million_krw"] / leave_summary["maternity_leave_users"]
        ).round(2)
        leave_summary["parental_leave_per_user_million_krw"] = (
            leave_summary["parental_leave_amount_million_krw"] / leave_summary["parental_leave_total_users"]
        ).round(2)
        leave_summary["female_parental_leave_per_user_million_krw"] = (
            leave_summary["female_parental_leave_amount_million_krw"] / leave_summary["female_parental_leave_users"]
        ).round(2)
        leave_summary["male_parental_leave_per_user_million_krw"] = (
            leave_summary["male_parental_leave_amount_million_krw"] / leave_summary["male_parental_leave_users"]
        ).round(2)
        write_csv(leave_summary, "parental_leave_summary.csv")
        charts["parental_leave_summary"] = leave_summary.to_dict("records")

        parental_leave_gender_users = leave_summary[
            [
                "year",
                "parental_leave_total_users",
                "female_parental_leave_users",
                "male_parental_leave_users",
                "male_parental_leave_share_pct",
            ]
        ].copy()
        write_csv(parental_leave_gender_users, "parental_leave_gender_users.csv")
        charts["parental_leave_gender_users"] = parental_leave_gender_users.to_dict("records")

        maternity_leave_support = leave_summary[
            [
                "year",
                "maternity_leave_users",
                "maternity_leave_amount_million_krw",
                "maternity_leave_per_user_million_krw",
            ]
        ].copy()
        write_csv(maternity_leave_support, "maternity_leave_support.csv")
        charts["maternity_leave_support"] = maternity_leave_support.to_dict("records")

        financing_pressure = leave_summary[
            [
                "year",
                "maternity_leave_users",
                "parental_leave_total_users",
                "maternity_leave_amount_million_krw",
                "parental_leave_amount_million_krw",
            ]
        ].copy()
        financing_pressure["maternity_leave_amount_trillion_krw"] = (
            financing_pressure["maternity_leave_amount_million_krw"] / 1_000_000
        ).round(3)
        financing_pressure["parental_leave_amount_trillion_krw"] = (
            financing_pressure["parental_leave_amount_million_krw"] / 1_000_000
        ).round(3)
        financing_pressure["total_maternity_parental_amount_trillion_krw"] = (
            (
                financing_pressure["maternity_leave_amount_million_krw"]
                + financing_pressure["parental_leave_amount_million_krw"]
            )
            / 1_000_000
        ).round(3)
        financing_pressure["parental_leave_share_pct"] = (
            financing_pressure["parental_leave_amount_million_krw"]
            / (
                financing_pressure["maternity_leave_amount_million_krw"]
                + financing_pressure["parental_leave_amount_million_krw"]
            )
            * 100
        ).round(1)
        write_csv(financing_pressure, "maternity_parental_leave_financing_pressure.csv")
        charts["maternity_parental_leave_financing_pressure"] = financing_pressure.to_dict("records")

        parental_leave_per_user_support = leave_summary[
            [
                "year",
                "parental_leave_per_user_million_krw",
                "female_parental_leave_per_user_million_krw",
                "male_parental_leave_per_user_million_krw",
                "parental_leave_amount_million_krw",
            ]
        ].copy()
        write_csv(parental_leave_per_user_support, "parental_leave_per_user_support.csv")
        charts["parental_leave_per_user_support"] = parental_leave_per_user_support.to_dict("records")

        access_gap = pd.DataFrame(
            [
                {
                    "group": "정규직 고용보험 가입",
                    "workers_10k": round(1384.5 * 0.918, 1),
                    "access_class": "상대적으로 제도 접근 가능",
                    "base_workers_10k": 1384.5,
                    "employment_insurance_rate_pct": 91.8,
                    "basis": "정규직 근로자 1,384.5만 명 × 고용보험 가입률 91.8%",
                },
                {
                    "group": "정규직 고용보험 미가입·별도제도",
                    "workers_10k": round(1384.5 * (1 - 0.918), 1),
                    "access_class": "고용보험 DB 밖 또는 별도 제도",
                    "base_workers_10k": 1384.5,
                    "employment_insurance_rate_pct": 8.2,
                    "basis": "정규직 근로자 중 고용보험 미가입분. 공무원·사립학교 교직원 등 별도 제도 대상이 섞일 수 있음",
                },
                {
                    "group": "비정규직 고용보험 가입",
                    "workers_10k": round(856.8 * 0.537, 1),
                    "access_class": "제도 접근 가능하나 사용 여건 취약",
                    "base_workers_10k": 856.8,
                    "employment_insurance_rate_pct": 53.7,
                    "basis": "비정규직 근로자 856.8만 명 × 고용보험 가입률 53.7%",
                },
                {
                    "group": "비정규직 고용보험 미가입",
                    "workers_10k": round(856.8 * (1 - 0.537), 1),
                    "access_class": "고용보험 기반 육아휴직급여 접근 취약",
                    "base_workers_10k": 856.8,
                    "employment_insurance_rate_pct": 46.3,
                    "basis": "비정규직 근로자 중 고용보험 미가입분",
                },
                {
                    "group": "비임금근로자",
                    "workers_10k": 655.4,
                    "access_class": "표준 고용보험 육아휴직급여 밖",
                    "base_workers_10k": 655.4,
                    "employment_insurance_rate_pct": None,
                    "basis": "비임금근로자 655.4만 명. 자영업자·무급가족종사자 등은 표준 임금근로자 육아휴직급여와 제도 구조가 다름",
                },
            ]
        )
        access_gap["share_of_wage_and_nonwage_workers_pct"] = (
            access_gap["workers_10k"] / access_gap["workers_10k"].sum() * 100
        ).round(1)
        write_csv(access_gap, "parental_leave_access_gap_2025.csv")
        charts["parental_leave_access_gap_2025"] = access_gap.to_dict("records")

    preschool_childcare_time = pd.DataFrame(
        [
            {
                "year": 2019,
                "husband_care_minutes": 62,
                "wife_care_minutes": 193,
                "husband_housework_minutes": 88,
                "wife_housework_minutes": 285,
            },
            {
                "year": 2024,
                "husband_care_minutes": 88,
                "wife_care_minutes": 219,
                "husband_housework_minutes": 113,
                "wife_housework_minutes": 314,
            },
        ]
    )
    preschool_childcare_time["husband_care_share_pct"] = (
        preschool_childcare_time["husband_care_minutes"]
        / (preschool_childcare_time["husband_care_minutes"] + preschool_childcare_time["wife_care_minutes"])
        * 100
    ).round(1)
    preschool_childcare_time["care_gap_minutes"] = (
        preschool_childcare_time["wife_care_minutes"] - preschool_childcare_time["husband_care_minutes"]
    )
    write_csv(preschool_childcare_time, "preschool_childcare_time_by_parent.csv")
    charts["preschool_childcare_time_by_parent"] = preschool_childcare_time.to_dict("records")

    dual_earner_child_housework_time = pd.DataFrame(
        [
            {"year": 2019, "husband_housework_minutes": 71, "wife_housework_minutes": 229},
            {"year": 2024, "husband_housework_minutes": 84, "wife_housework_minutes": 212},
        ]
    )
    dual_earner_child_housework_time["husband_housework_share_pct"] = (
        dual_earner_child_housework_time["husband_housework_minutes"]
        / (
            dual_earner_child_housework_time["husband_housework_minutes"]
            + dual_earner_child_housework_time["wife_housework_minutes"]
        )
        * 100
    ).round(1)
    dual_earner_child_housework_time["housework_gap_minutes"] = (
        dual_earner_child_housework_time["wife_housework_minutes"]
        - dual_earner_child_housework_time["husband_housework_minutes"]
    )
    write_csv(dual_earner_child_housework_time, "dual_earner_child_housework_time.csv")
    charts["dual_earner_child_housework_time"] = dual_earner_child_housework_time.to_dict("records")

    elderly_labor_path = DERIVED / "elderly_labor_dt_1de8031s_trends.csv"
    if elderly_labor_path.exists():
        elderly_labor = pd.read_csv(elderly_labor_path)
        write_csv(elderly_labor, "elderly_labor_dt_1de8031s_trends.csv")
        charts["elderly_labor_dt_1de8031s"] = elderly_labor.to_dict("records")

    elderly_labor_summary_path = DERIVED / "elderly_labor_dt_1de8031s_summary.csv"
    if elderly_labor_summary_path.exists():
        elderly_labor_summary = pd.read_csv(elderly_labor_summary_path)
        write_csv(elderly_labor_summary, "elderly_labor_dt_1de8031s_summary.csv")
        charts["elderly_labor_dt_1de8031s_summary"] = elderly_labor_summary.to_dict("records")

    for chart_id, csv_name in [
        ("elderly_activity_life_course_indicators", "elderly_activity_life_course_indicators.csv"),
        ("elderly_activity_exit_reasons_2025", "elderly_activity_exit_reasons_2025.csv"),
        ("elderly_activity_future_work_reasons_2025", "elderly_activity_future_work_reasons_2025.csv"),
        ("elderly_activity_job_preferences_2025", "elderly_activity_job_preferences_2025.csv"),
        ("elderly_employment_structure_2025", "elderly_employment_structure_2025.csv"),
    ]:
        path = DERIVED / csv_name
        if path.exists():
            frame = pd.read_csv(path)
            write_csv(frame, csv_name)
            charts[chart_id] = frame.to_dict("records")

    regional_elderly_labor_path = DERIVED / "elderly_regional_labor_60plus_trends.csv"
    if regional_elderly_labor_path.exists():
        regional_elderly_labor = pd.read_csv(regional_elderly_labor_path)
        write_csv(regional_elderly_labor, "elderly_regional_labor_60plus_trends.csv")
        charts["elderly_regional_labor_60plus_trends"] = regional_elderly_labor.to_dict("records")

    regional_elderly_slopes_path = DERIVED / "elderly_regional_labor_60plus_slopes.csv"
    if regional_elderly_slopes_path.exists():
        regional_elderly_slopes = pd.read_csv(regional_elderly_slopes_path)
        write_csv(regional_elderly_slopes, "elderly_regional_labor_60plus_slopes.csv")
        charts["elderly_regional_labor_60plus_slopes"] = regional_elderly_slopes.to_dict("records")

    nta_path = DATA / "national_transfer_accounts_DT_1NTA2003.csv"
    if nta_path.exists():
        nta = pd.read_csv(nta_path)
        nta = nta[nta["C1_NM"] == "공공보건소비"].copy()
        nta["year"] = pd.to_numeric(nta["PRD_DE"], errors="coerce").astype("Int64")
        nta["amount_thousand_krw_per_person"] = pd.to_numeric(nta["DT"], errors="coerce")

        def parse_nta_age(label: object) -> int | None:
            text = str(label)
            if "85" in text:
                return 85
            match = re.search(r"\d+", text)
            return int(match.group(0)) if match else None

        def nta_age_group(age: object) -> str:
            age = int(age)
            if age <= 14:
                return "0-14세"
            if age <= 44:
                return "15-44세"
            if age <= 64:
                return "45-64세"
            if age <= 74:
                return "65-74세"
            if age <= 84:
                return "75-84세"
            return "85세 이상"

        nta["age"] = nta["C2_NM"].map(parse_nta_age)
        nta = nta.dropna(subset=["year", "age", "amount_thousand_krw_per_person"]).copy()
        nta["age"] = nta["age"].astype(int)
        nta["age_label"] = nta["C2_NM"].replace({"85세이상": "85세 이상"})
        selected_nta_years = [2010, 2015, 2020, 2022]
        nta_profile = nta[nta["year"].isin(selected_nta_years)].copy()
        nta_profile["amount_million_krw_per_person"] = (nta_profile["amount_thousand_krw_per_person"] / 1000).round(3)
        nta_profile = nta_profile[
            ["year", "age", "age_label", "amount_thousand_krw_per_person", "amount_million_krw_per_person"]
        ].sort_values(["year", "age"])
        write_csv(nta_profile, "nta_public_health_age_profile.csv")
        charts["nta_public_health_age_profile"] = nta_profile.to_dict("records")

        nta_groups = nta.copy()
        nta_groups["age_group"] = nta_groups["age"].map(nta_age_group)
        group_order = ["0-14세", "15-44세", "45-64세", "65-74세", "75-84세", "85세 이상"]
        nta_group_trend = (
            nta_groups.groupby(["year", "age_group"], as_index=False)["amount_thousand_krw_per_person"]
            .mean()
            .sort_values(["year", "age_group"])
        )
        nta_group_trend["amount_thousand_krw_per_person"] = nta_group_trend["amount_thousand_krw_per_person"].round(1)
        nta_group_trend["amount_million_krw_per_person"] = (
            nta_group_trend["amount_thousand_krw_per_person"] / 1000
        ).round(3)
        nta_group_trend["age_group_order"] = nta_group_trend["age_group"].map(
            {name: index for index, name in enumerate(group_order, start=1)}
        )
        nta_group_trend = nta_group_trend.sort_values(["age_group_order", "year"])
        write_csv(nta_group_trend, "nta_public_health_age_group_trend.csv")
        charts["nta_public_health_age_group_trend"] = nta_group_trend.to_dict("records")

    elderly_pension_path = DERIVED / "elderly_pension_dt_1de8051s_trends.csv"
    if elderly_pension_path.exists():
        elderly_pension = pd.read_csv(elderly_pension_path)
        write_csv(elderly_pension, "elderly_pension_dt_1de8051s_trends.csv")
        charts["elderly_pension_dt_1de8051s"] = elderly_pension.to_dict("records")

    elderly_pension_distribution_path = DERIVED / "elderly_pension_dt_1de8051s_distribution.csv"
    if elderly_pension_distribution_path.exists():
        elderly_pension_distribution = pd.read_csv(elderly_pension_distribution_path)
        write_csv(elderly_pension_distribution, "elderly_pension_dt_1de8051s_distribution.csv")
        charts["elderly_pension_amount_distribution"] = elderly_pension_distribution.to_dict("records")

    multi = pd.read_csv(DATA / "international_marriage_DT_1BB0006.csv")
    multi = multi[(multi["C1_NM"] == "전국") & (multi["ITM_ID"] == "T02")].copy()
    multi = multi.rename(columns={"PRD_DE": "year", "DT": "multicultural_birth_share"})
    multi["multicultural_birth_share"] = pd.to_numeric(multi["multicultural_birth_share"], errors="coerce")
    multi = multi[["year", "multicultural_birth_share"]].sort_values("year")
    write_csv(multi, "multicultural_birth_rate.csv")
    charts["multicultural_birth_rate"] = multi.to_dict("records")

    childcare_raw = pd.read_csv(DATA / "childcare_children_DT_15407_NN002.csv")
    childcare_raw["type_code"] = childcare_raw["C1"].astype(str).str.zfill(2)
    childcare_raw["childcare_children"] = pd.to_numeric(childcare_raw["DT"], errors="coerce")
    childcare = childcare_raw[childcare_raw["C1_NM"] == "합계"].copy()
    childcare = childcare.rename(columns={"PRD_DE": "year"})
    childcare = childcare[["year", "childcare_children"]].sort_values("year")
    write_csv(childcare, "childcare_children.csv")
    charts["childcare_children"] = childcare.to_dict("records")

    facilities_raw = pd.read_csv(DATA / "parental_leave_DT_15407_NN001.csv")
    facilities_raw["type_code"] = facilities_raw["C1"].astype(str).str.zfill(2)
    facilities_raw["childcare_facilities"] = pd.to_numeric(facilities_raw["DT"], errors="coerce")
    facilities = facilities_raw[facilities_raw["C1_NM"] == "합계"].copy()
    facilities = facilities.rename(columns={"PRD_DE": "year"})
    childcare_capacity = childcare.merge(facilities[["year", "childcare_facilities"]], on="year", how="inner")
    childcare_capacity["children_per_facility"] = (childcare_capacity["childcare_children"] / childcare_capacity["childcare_facilities"]).round(2)
    write_csv(childcare_capacity, "childcare_capacity_pressure.csv")
    charts["childcare_capacity_pressure"] = childcare_capacity.to_dict("records")

    type_order = ["02", "03", "04", "05", "06", "07", "08"]
    childcare_supply_by_type = facilities_raw[facilities_raw["type_code"].isin(type_order)].copy()
    childcare_supply_by_type = childcare_supply_by_type.rename(columns={"PRD_DE": "year", "C1_NM": "type"})
    childcare_supply_by_type = childcare_supply_by_type[["year", "type_code", "type", "childcare_facilities"]].sort_values(["year", "type_code"])
    write_csv(childcare_supply_by_type, "childcare_supply_by_type.csv")
    charts["childcare_supply_by_type"] = childcare_supply_by_type.to_dict("records")

    childcare_users_by_type = childcare_raw[childcare_raw["type_code"].isin(type_order)].copy()
    childcare_users_by_type = childcare_users_by_type.rename(columns={"PRD_DE": "year", "C1_NM": "type"})
    childcare_users_by_type = childcare_users_by_type[["year", "type_code", "type", "childcare_children"]].sort_values(["year", "type_code"])
    write_csv(childcare_users_by_type, "childcare_users_by_type.csv")
    charts["childcare_users_by_type"] = childcare_users_by_type.to_dict("records")

    childcare_supply_users_by_type = childcare_supply_by_type.merge(
        childcare_users_by_type,
        on=["year", "type_code", "type"],
        how="inner",
    )
    childcare_supply_users_by_type["children_per_facility"] = (
        childcare_supply_users_by_type["childcare_children"] / childcare_supply_users_by_type["childcare_facilities"]
    ).round(2)
    year_totals = childcare_supply_users_by_type.groupby("year", as_index=False)[["childcare_facilities", "childcare_children"]].sum()
    year_totals = year_totals.rename(columns={"childcare_facilities": "total_facilities", "childcare_children": "total_children"})
    childcare_supply_users_by_type = childcare_supply_users_by_type.merge(year_totals, on="year", how="left")
    childcare_supply_users_by_type["facility_share"] = (
        childcare_supply_users_by_type["childcare_facilities"] / childcare_supply_users_by_type["total_facilities"] * 100
    ).round(2)
    childcare_supply_users_by_type["children_share"] = (
        childcare_supply_users_by_type["childcare_children"] / childcare_supply_users_by_type["total_children"] * 100
    ).round(2)
    write_csv(childcare_supply_users_by_type, "childcare_supply_users_by_type.csv")
    charts["childcare_supply_users_by_type"] = childcare_supply_users_by_type.to_dict("records")

    special_childcare_path = DATA / "special_childcare_DT_15407_NN009.csv"
    if special_childcare_path.exists():
        special_raw = pd.read_csv(special_childcare_path)
        special_raw = special_raw.rename(columns={"PRD_DE": "year", "C1": "time_type_code", "C1_NM": "time_type"})
        special_raw["value"] = pd.to_numeric(special_raw["DT"], errors="coerce")
        special_raw["year"] = pd.to_numeric(special_raw["year"], errors="coerce")
        time_types = ["야간 연장", "24시간", "휴일"]
        special_facilities = special_raw[
            (special_raw["ITM_NM"] == "어린이집수") & (special_raw["time_type"].isin(time_types))
        ].copy()
        special_facilities = special_facilities.rename(columns={"value": "special_childcare_facilities"})
        special_facilities = special_facilities[
            ["year", "time_type_code", "time_type", "special_childcare_facilities"]
        ].sort_values(["year", "time_type_code"])
        special_facilities = special_facilities.merge(
            facilities[["year", "childcare_facilities"]],
            on="year",
            how="left",
        )
        special_facilities["share_of_total_facilities_pct"] = (
            special_facilities["special_childcare_facilities"] / special_facilities["childcare_facilities"] * 100
        ).round(2)
        write_csv(special_facilities, "childcare_time_flexible_facilities.csv")
        charts["childcare_time_flexible_facilities"] = special_facilities.to_dict("records")

        special_children = special_raw[
            (special_raw["ITM_NM"] == "아동현원") & (special_raw["time_type"].isin(time_types))
        ].copy()
        special_children = special_children.rename(columns={"value": "special_childcare_children"})
        special_children = special_children[["year", "time_type_code", "time_type", "special_childcare_children"]]
        special_children = special_children.merge(childcare, on="year", how="left")
        special_children["share_of_total_children_pct"] = (
            special_children["special_childcare_children"] / special_children["childcare_children"] * 100
        ).round(3)
        write_csv(special_children, "childcare_time_flexible_children.csv")
        charts["childcare_time_flexible_children"] = special_children.to_dict("records")

    fiscal = pd.read_csv(DATA / "openfiscal_population_budget.csv")
    fiscal = fiscal.rename(columns={"ACNT_YR": "year", "NAT_DB_AMT": "national_debt", "FNC_DB_AMT": "financial_debt"})
    fiscal = fiscal[["year", "national_debt", "financial_debt"]].sort_values("year")
    write_csv(fiscal, "openfiscal_debt_context.csv")
    charts["openfiscal_debt_context"] = fiscal.to_dict("records")

    aging_budget_path = DERIVED / "openfiscal_aging_budget_trends.csv"
    if aging_budget_path.exists():
        aging_budget = pd.read_csv(aging_budget_path)
        charts["openfiscal_aging_budget_trends"] = aging_budget.to_dict("records")

    aging_budget_top_path = DERIVED / "openfiscal_aging_budget_top_programs_latest.csv"
    if aging_budget_top_path.exists():
        aging_budget_top = pd.read_csv(aging_budget_top_path)
        charts["openfiscal_aging_budget_top_programs"] = aging_budget_top.to_dict("records")

    fiscal_pressure = fiscal.merge(pressure[["year", "older_share", "old_age_dependency_ratio"]], on="year", how="inner")
    if not fiscal_pressure.empty:
        base_debt = fiscal_pressure.loc[fiscal_pressure["year"].idxmin(), "national_debt"]
        base_older = fiscal_pressure.loc[fiscal_pressure["year"].idxmin(), "older_share"]
        fiscal_pressure["national_debt_index"] = (fiscal_pressure["national_debt"] / base_debt * 100).round(1)
        fiscal_pressure["older_share_index"] = (fiscal_pressure["older_share"] / base_older * 100).round(1)
    write_csv(fiscal_pressure, "fiscal_aging_pressure.csv")
    charts["fiscal_aging_pressure"] = fiscal_pressure.to_dict("records")

    vacant = pd.read_csv(DATA / "elderly_economic_activity.csv")
    vacant = vacant[(vacant["C1_NM"] == "전국") & (vacant["ITM_ID"] == "T10")].copy()
    vacant = vacant.rename(columns={"PRD_DE": "year", "DT": "vacant_housing_rate"})
    vacant = vacant[["year", "vacant_housing_rate"]]
    write_csv(vacant, "vacant_housing_rate.csv")
    charts["vacant_housing_rate"] = vacant.to_dict("records")

    vacant_raw = pd.read_csv(DATA / "elderly_economic_activity.csv")
    vacant_policy = vacant_raw[vacant_raw["C1_NM"] == "전국"].copy()
    vacant_policy["DT"] = pd.to_numeric(vacant_policy["DT"], errors="coerce")
    vacant_policy = vacant_policy.pivot_table(index="PRD_DE", columns="ITM_ID", values="DT", aggfunc="first").reset_index()
    vacant_policy = vacant_policy.rename(columns={"PRD_DE": "year", "T10": "vacant_housing_rate", "T20": "vacant_housing_count", "T30": "total_housing_count"})
    vacant_policy = vacant_policy[["year", "vacant_housing_rate", "vacant_housing_count", "total_housing_count"]].sort_values("year")
    write_csv(vacant_policy, "vacant_housing_policy.csv")
    charts["vacant_housing_policy"] = vacant_policy.to_dict("records")

    kosis_2022 = vacant_policy.loc[vacant_policy["year"] == 2022, "vacant_housing_count"]
    kosis_vacant_2022 = float(kosis_2022.iloc[0]) if not kosis_2022.empty else 1_451_554
    molit_vacant_2022 = 132_052
    definition_gap = pd.DataFrame(
        [
            {
                "definition": "KOSIS 미거주주택",
                "count": kosis_vacant_2022,
                "definition_note": "조사시점에 사람이 살지 않는 주택",
            },
            {
                "definition": "국토부 등 장기 빈집",
                "count": molit_vacant_2022,
                "definition_note": "1년 이상 거주 또는 사용하지 않은 주택",
            },
        ]
    )
    definition_gap["share_of_kosis_pct"] = (definition_gap["count"] / kosis_vacant_2022 * 100).round(1)
    write_csv(definition_gap, "vacant_housing_definition_gap_2022.csv")
    charts["vacant_housing_definition_gap_2022"] = definition_gap.to_dict("records")

    molit_vacant = pd.DataFrame(
        [
            {"area_type": "도시지역", "vacant_housing_count": 42356},
            {"area_type": "농촌지역", "vacant_housing_count": 66024},
            {"area_type": "어촌지역", "vacant_housing_count": 23672},
        ]
    )
    molit_vacant["share_pct"] = (molit_vacant["vacant_housing_count"] / molit_vacant["vacant_housing_count"].sum() * 100).round(1)
    molit_vacant["year"] = 2022
    write_csv(molit_vacant, "molit_vacant_housing_2022.csv")
    charts["molit_vacant_housing_2022"] = molit_vacant.to_dict("records")

    foreigners = pd.read_csv(DATA / "registered_foreigners_DT_1B040A11.csv")
    foreigners = foreigners[(foreigners["C1_NM"] == "총계") & (foreigners["C2_NM"] == "계") & (foreigners["C3_NM"] == "총계")].copy()
    foreigners["DT"] = pd.to_numeric(foreigners["DT"], errors="coerce")
    foreigners = foreigners.rename(columns={"PRD_DE": "year", "DT": "registered_foreigners"})
    foreigners = foreigners[["year", "registered_foreigners"]].drop_duplicates().sort_values("year")
    write_csv(foreigners, "foreigner_registered_total.csv")
    charts["foreigner_registered_total"] = foreigners.to_dict("records")

    households_path = DATA / "future_households_DT_1BZ0503.csv"
    if households_path.exists():
        households = pd.read_csv(households_path)
        households = households[households["C2_NM"] == "합계"].copy()
        households["DT"] = pd.to_numeric(households["DT"], errors="coerce")
        households = households.pivot_table(index="PRD_DE", columns="ITM_NM", values="DT", aggfunc="first").reset_index()
        households = households.rename(columns={"PRD_DE": "year", "계": "total_households", "1인": "one_person_households", "2인": "two_person_households", "4인": "four_person_households"})
        households = households[["year", "total_households", "one_person_households", "two_person_households", "four_person_households"]].sort_values("year")
        write_csv(households, "future_households_policy.csv")
        charts["future_households_policy"] = households.to_dict("records")

    household_head_age_path = DATA / "household_head_age_size_DT_1JC1511.csv"
    if household_head_age_path.exists():
        head_age = pd.read_csv(household_head_age_path, dtype={"C1": str, "C2": str, "ITM_ID": str})
        head_age["year"] = pd.to_numeric(head_age["PRD_DE"], errors="coerce")
        head_age["value"] = pd.to_numeric(head_age["DT"], errors="coerce")
        head_age["C1"] = head_age["C1"].astype(str).str.zfill(2)
        head_age["C2"] = head_age["C2"].astype(str).str.zfill(3)
        head_age = head_age[(head_age["C1"] == "00") & head_age["year"].between(2015, 2024)].copy()
        young_codes = ["020", "025", "030", "035"]  # 20-34세
        older_codes = ["070", "075", "080", "085", "086"]  # 65세 이상
        rows = []
        for year, group in head_age.groupby("year"):
            total_households = float(group.loc[(group["ITM_ID"] == "T100") & (group["C2"] == "000"), "value"].sum())
            one_person_households = float(group.loc[(group["ITM_ID"] == "T210") & (group["C2"] == "000"), "value"].sum())
            young_head_households = float(group.loc[(group["ITM_ID"] == "T100") & (group["C2"].isin(young_codes)), "value"].sum())
            older_head_households = float(group.loc[(group["ITM_ID"] == "T100") & (group["C2"].isin(older_codes)), "value"].sum())
            young_one_person_households = float(group.loc[(group["ITM_ID"] == "T210") & (group["C2"].isin(young_codes)), "value"].sum())
            older_one_person_households = float(group.loc[(group["ITM_ID"] == "T210") & (group["C2"].isin(older_codes)), "value"].sum())
            rows.append(
                {
                    "year": int(year),
                    "total_households": int(total_households),
                    "one_person_households": int(one_person_households),
                    "young_head_households_20_34": int(young_head_households),
                    "older_head_households_65plus": int(older_head_households),
                    "young_one_person_households_20_34": int(young_one_person_households),
                    "older_one_person_households_65plus": int(older_one_person_households),
                    "older_head_share_pct": round(older_head_households / total_households * 100, 2),
                    "young_head_share_pct": round(young_head_households / total_households * 100, 2),
                    "one_person_share_pct": round(one_person_households / total_households * 100, 2),
                    "young_one_person_share_of_total_pct": round(young_one_person_households / total_households * 100, 2),
                    "older_one_person_share_of_total_pct": round(older_one_person_households / total_households * 100, 2),
                    "young_one_person_share_of_one_person_pct": round(young_one_person_households / one_person_households * 100, 2),
                    "older_one_person_share_of_one_person_pct": round(older_one_person_households / one_person_households * 100, 2),
                }
            )
        head_age_summary = pd.DataFrame(rows).sort_values("year")
        for column in [
            "total_households",
            "one_person_households",
            "young_one_person_households_20_34",
            "older_one_person_households_65plus",
            "older_head_households_65plus",
        ]:
            head_age_summary[f"{column}_index_2015_100"] = (
                head_age_summary[column] / head_age_summary[column].iloc[0] * 100
            ).round(2)
            head_age_summary[f"{column}_change_pct_since_2015"] = (
                (head_age_summary[column] / head_age_summary[column].iloc[0] - 1) * 100
            ).round(2)
        write_csv(head_age_summary, "household_head_age_shift.csv")
        charts["household_head_age_shift"] = head_age_summary.to_dict("records")
        charts["household_one_person_age_index"] = head_age_summary.to_dict("records")

    household_census_path = DATA / "households_INH_1JC1501.csv"
    sigungu_population_path = DATA / "sigungu_population_2004_2024.csv"
    if household_census_path.exists() and sigungu_population_path.exists():
        household_census = pd.read_csv(household_census_path, dtype={"C1": str})
        household_census["year"] = pd.to_numeric(household_census["PRD_DE"], errors="coerce")
        household_census["households"] = pd.to_numeric(household_census["DT"], errors="coerce")
        household_census["C1"] = household_census["C1"].astype(str).str.zfill(2)
        household_sido = household_census[
            household_census["C1"].str.fullmatch(r"\d{2}")
        ][["year", "C1", "C1_NM", "households"]].rename(columns={"C1_NM": "region"})

        sigungu_population = pd.read_csv(sigungu_population_path, dtype={"C1": str})
        sigungu_population["year"] = pd.to_numeric(sigungu_population["year"], errors="coerce")
        sigungu_population["population"] = pd.to_numeric(sigungu_population["population"], errors="coerce")
        sigungu_population["C1"] = sigungu_population["C1"].astype(str).str.zfill(5)
        sigungu_population["family_code"] = sigungu_population["C1"].str[:4]
        bottom_rows = []
        for _, year_group in sigungu_population.groupby("year"):
            year_group = year_group.copy()
            sibling_sum = (
                year_group[~year_group["C1"].str.endswith("0")]
                .groupby("family_code")["population"]
                .sum()
                .to_dict()
            )
            aggregate_with_child = year_group["C1"].str.endswith("0") & year_group.apply(
                lambda row: sibling_sum.get(row["family_code"], 0) > row["population"] * 0.5,
                axis=1,
            )
            zero_auxiliary = (~year_group["C1"].str.endswith("0")) & (year_group["population"] == 0)
            bottom_rows.append(year_group[~aggregate_with_child & ~zero_auxiliary].copy())
        bottom_population = pd.concat(bottom_rows, ignore_index=True)
        province_name = {
            "11": "서울특별시",
            "26": "부산광역시",
            "27": "대구광역시",
            "28": "인천광역시",
            "29": "광주광역시",
            "30": "대전광역시",
            "31": "울산광역시",
            "36": "세종특별자치시",
            "41": "경기도",
            "51": "강원특별자치도",
            "43": "충청북도",
            "44": "충청남도",
            "52": "전북특별자치도",
            "46": "전라남도",
            "47": "경상북도",
            "48": "경상남도",
            "50": "제주특별자치도",
        }
        bottom_population["region"] = bottom_population["C1"].str[:2].map(province_name)
        population_sido = (
            bottom_population.dropna(subset=["region"])
            .groupby(["year", "region"], as_index=False)["population"]
            .sum()
        )
        national_population = bottom_population.groupby("year", as_index=False)["population"].sum()
        national_population["region"] = "전국"
        population_all = pd.concat([national_population, population_sido], ignore_index=True)

        household_population = household_sido.merge(population_all, on=["year", "region"], how="inner")
        household_population["area_group"] = np.where(
            household_population["region"].isin(["서울특별시", "인천광역시", "경기도"]),
            "수도권",
            np.where(household_population["region"] == "전국", "전국", "비수도권"),
        )
        household_population["average_household_size"] = (
            household_population["population"] / household_population["households"]
        ).round(3)
        base_household_population = household_population[household_population["year"] == 2015][
            ["region", "households", "population"]
        ].rename(columns={"households": "base_households", "population": "base_population"})
        household_population = household_population.merge(base_household_population, on="region", how="left")
        household_population["household_index_2015_100"] = (
            household_population["households"] / household_population["base_households"] * 100
        ).round(2)
        household_population["population_index_2015_100"] = (
            household_population["population"] / household_population["base_population"] * 100
        ).round(2)
        household_population["index_gap_household_minus_population"] = (
            household_population["household_index_2015_100"]
            - household_population["population_index_2015_100"]
        ).round(2)
        household_population["household_change_pct_since_2015"] = (
            household_population["household_index_2015_100"] - 100
        ).round(2)
        household_population["population_change_pct_since_2015"] = (
            household_population["population_index_2015_100"] - 100
        ).round(2)
        household_population = household_population[
            [
                "year",
                "region",
                "area_group",
                "households",
                "population",
                "average_household_size",
                "household_index_2015_100",
                "population_index_2015_100",
                "index_gap_household_minus_population",
                "household_change_pct_since_2015",
                "population_change_pct_since_2015",
            ]
        ].sort_values(["region", "year"])
        write_csv(household_population, "household_population_gap_all_regions.csv")

        household_national = household_population[household_population["region"] == "전국"].copy()
        write_csv(household_national, "household_population_gap_national.csv")
        charts["household_population_gap_national"] = household_national.to_dict("records")

        household_regions = household_population[
            (household_population["year"] == 2024)
            & (household_population["region"] != "전국")
        ].copy()
        household_regions["gap_change_pct"] = (
            household_regions["household_change_pct_since_2015"]
            - household_regions["population_change_pct_since_2015"]
        ).round(2)
        household_regions = household_regions.sort_values("gap_change_pct", ascending=False)
        write_csv(household_regions, "household_population_gap_regions.csv")
        charts["household_population_gap_regions"] = household_regions.to_dict("records")

    return charts


def nav_html(current: str = "") -> str:
    parts = ['<nav class="toc" aria-label="책 목차">', '<h2 class="toc-title">인구·저출산·고령화</h2>', '<a href="../index.html">표지</a>']
    for chapter in BOOK:
        cls = "chapter active" if current == chapter["file"] else "chapter"
        parts.append(f'<a class="{cls}" href="../chapters/{chapter["file"]}">{chapter["no"]}. {esc(chapter["title"])}</a>')
        for section in chapter["sections"]:
            active = " active" if current == section["file"] else ""
            parts.append(f'<a class="toc-section{active}" href="../sections/{section["file"]}">{section["no"]} {esc(section["title"])}</a>')
    appendix_active = " active" if current == APPENDIX_FILE else ""
    parts.append(f'<a class="chapter{appendix_active}" href="../sections/{APPENDIX_FILE}">부록. 자료와 분석 설계</a>')
    parts.append("</nav>")
    return "\n".join(parts)


def shell(title: str, body: str, current: str, rel: str = "..") -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="stylesheet" href="{rel}/site.css?v={ASSET_VERSION}">
  <link rel="stylesheet" href="{rel}/_book_pages.css?v={ASSET_VERSION}">
</head>
<body>
  <div class="layout">
    {nav_html(current)}
    <main class="page book-page">
      {body}
    </main>
  </div>
  <script src="{rel}/vendor/chart.umd.min.js"></script>
  <script src="{rel}/question_plan.js?v={ASSET_VERSION}"></script>
  <script src="{rel}/book_chart_data.js?v={ASSET_VERSION}"></script>
  <script src="{rel}/data/geo/sigungu_topo.js?v={ASSET_VERSION}"></script>
  <script src="{rel}/book_pages.js?v={ASSET_VERSION}"></script>
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [["\\\\(", "\\\\)"]],
        displayMath: [["\\\\[", "\\\\]"]]
      }},
      options: {{ skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code"] }}
    }};
  </script>
  <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</body>
</html>
"""


def aging_budget_program_table_html() -> str:
    path = DATA / "openfiscal_VW_OPFI940_aging_budget_matches.csv"
    if not path.exists():
        return ""
    matches = pd.read_csv(path)
    if matches.empty or "FSCL_YY" not in matches.columns:
        return ""
    latest_year = int(pd.to_numeric(matches["FSCL_YY"], errors="coerce").max())
    latest = matches[pd.to_numeric(matches["FSCL_YY"], errors="coerce") == latest_year].copy()
    if latest.empty:
        return ""
    latest["budget_amount_thousand_krw"] = pd.to_numeric(latest["budget_amount_thousand_krw"], errors="coerce").fillna(0)
    table = (
        latest.groupby(["SACTV_NM", "aging_budget_category"], dropna=False)
        .agg(
            budget_amount_thousand_krw=("budget_amount_thousand_krw", "sum"),
            offices=("OFFC_NM", lambda values: ", ".join(sorted(set(map(str, values)))[:4])),
        )
        .reset_index()
        .rename(columns={"SACTV_NM": "program_name", "aging_budget_category": "category"})
        .sort_values("budget_amount_thousand_krw", ascending=False)
    )
    table["year"] = latest_year
    table["budget_amount_trillion_krw"] = (table["budget_amount_thousand_krw"] / 1_000_000_000).round(3)
    table["budget_amount_100m_krw"] = (table["budget_amount_thousand_krw"] / 100_000).round(1)
    out_path = DERIVED / "openfiscal_aging_budget_programs_latest.csv"
    write_csv(
        table[
            [
                "year",
                "program_name",
                "category",
                "offices",
                "budget_amount_thousand_krw",
                "budget_amount_trillion_krw",
                "budget_amount_100m_krw",
            ]
        ],
        out_path.name,
    )
    total_trillion = table["budget_amount_thousand_krw"].sum() / 1_000_000_000
    total_100m = table["budget_amount_thousand_krw"].sum() / 100_000
    rows = []
    for idx, row in enumerate(table.to_dict("records"), start=1):
        rows.append(
            f"""<tr>
  <td class="num">{idx}</td>
  <td>{esc(row["program_name"])}</td>
  <td>{esc(row["category"])}</td>
  <td>{esc(row["offices"])}</td>
  <td class="num">{float(row["budget_amount_trillion_krw"]):,.3f}</td>
  <td class="num">{float(row["budget_amount_100m_krw"]):,.1f}</td>
</tr>"""
        )
    return f"""<section class="panel program-table-panel">
  <h2>고령화 관련 세부사업명과 예산 규모</h2>
  <p class="source-note">{latest_year}년 열린재정 세부사업 예산편성현황에서 노인·고령·기초연금·장기요양·치매 등 키워드로 추출한 전체 사업이다. 금액은 Y_YY_DFN_MEDI_KCUR_AMT를 기준으로 집계했다.</p>
  <div class="chart-actions table-actions">
    <a class="csv-button" href="../data/derived/{out_path.name}" download>CSV 다운로드</a>
    <span>출처: 열린재정 VW_OPFI940 세부사업 예산편성현황(총지출)</span>
  </div>
  <div class="data-table-wrap">
    <table class="data-table program-table">
      <thead>
        <tr>
          <th>순위</th>
          <th>세부사업명</th>
          <th>유형</th>
          <th>소관</th>
          <th>예산액(조원)</th>
          <th>예산액(억원)</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
      <tfoot>
        <tr>
          <th colspan="4">합계</th>
          <th class="num">{total_trillion:,.3f}</th>
          <th class="num">{total_100m:,.1f}</th>
        </tr>
      </tfoot>
    </table>
  </div>
</section>"""


def default_chapter_markdown(chapter: dict) -> str:
    lines = list(CHAPTER_NARRATIVE.get(chapter["file"], []))
    if chapter["sections"]:
        lines.append("## 이 장에서 읽을 절")
        for section in chapter["sections"]:
            lines.append(f"- [{section['no']}. {section['title']}](../sections/{section['file']})")
    return "\n\n".join(lines).strip() + "\n"


def default_section_markdown(chapter: dict, section: dict) -> str:
    lines: list[str] = []
    analysis = SECTION_ANALYSIS.get(section["file"], {})
    narrative = SECTION_NARRATIVE.get(section["file"], {})
    reading_note = SECTION_READING_NOTE.get(section["file"], [])
    supplemental = SECTION_SUPPLEMENTAL_CHARTS.get(section["file"], [])
    front_context = SECTION_FRONT_CONTEXT.get(section["file"], {})
    independent = SECTION_INDEPENDENT_ANALYSIS.get(section["file"], {})

    if narrative:
        lines.append(f"## {narrative['kicker']}")
        lines.extend(narrative["paragraphs"])
    elif analysis:
        lines.append(f"## {analysis['heading']}")
        lines.extend(analysis["paragraphs"])

    if front_context:
        lines.append(f"## {front_context['heading']}")
        lines.extend(front_context["paragraphs"])
        lines.append(chart_shortcode(front_context["chart"]))

    lines.append(chart_shortcode(section["chart"]))

    if reading_note:
        lines.append("## 본문 해석")
        lines.extend(reading_note)

    for chart_id in supplemental:
        lines.append(chart_shortcode(chart_id, "small"))

    if independent:
        lines.append(f"## {independent['heading']}")
        lines.extend(independent["paragraphs"])
        lines.append(chart_shortcode(independent["chart"]))

    if section["file"] == "section-5-4-aging-budget.html":
        lines.append("{{aging_budget_program_table}}")

    return "\n\n".join(lines).strip() + "\n"


def ensure_markdown_manuscripts() -> None:
    CHAPTER_MANUSCRIPTS.mkdir(parents=True, exist_ok=True)
    SECTION_MANUSCRIPTS.mkdir(parents=True, exist_ok=True)
    readme = MANUSCRIPTS / "README.md"
    if not readme.exists():
        readme.write_text(
            """# 마크다운 원고 편집 안내

이 폴더의 `chapters`와 `sections`에 있는 `.md` 파일이 책의 원고 원천입니다.

- 원고를 수정한 뒤 `python scripts\\build_book_pages.py`를 실행하면 HTML에 반영됩니다.
- 그림은 원하는 문단 위치에 `{{chart:차트ID}}` 형식으로 넣습니다.
- 작은 보조 그림은 `{{chart:차트ID|small}}`처럼 넣을 수 있습니다.
- 일반 이미지도 `![그림 설명](../data/example.png)` 형식으로 넣을 수 있습니다.
- 표는 일반 마크다운 표 문법을 사용할 수 있습니다.
- 5.4절의 고령화 예산 사업 표는 `{{aging_budget_program_table}}`로 삽입합니다.

차트 ID와 CSV·출처 정보는 `scripts/build_book_pages.py`의 `CHART_META`에 정의되어 있습니다.
""",
            encoding="utf-8",
        )
    for chapter in BOOK:
        path = chapter_manuscript_path(chapter)
        if not path.exists():
            path.write_text(default_chapter_markdown(chapter), encoding="utf-8")
        for section in chapter["sections"]:
            section_path = section_manuscript_path(section)
            if not section_path.exists():
                section_path.write_text(default_section_markdown(chapter, section), encoding="utf-8")


def section_body(chapter: dict, section: dict) -> str:
    manuscript = section_manuscript_path(section)
    if manuscript.exists():
        body = render_markdown(manuscript.read_text(encoding="utf-8"), rel="..")
        return f"""<section class="section-header-block">
  <p class="series">Chapter {chapter["no"]}</p>
  <h1>{section["no"]}. {esc(section["title"])}</h1>
  <p class="lead">{esc(chapter["thesis"])}</p>
  {page_feedback_link(section["no"], section["title"], section["file"])}
</section>
<div class="markdown-manuscript">
{body}
</div>"""
    meta = CHART_META[section["chart"]]
    analysis = SECTION_ANALYSIS.get(section["file"], {})
    narrative = SECTION_NARRATIVE.get(section["file"], {})
    reading_note = SECTION_READING_NOTE.get(section["file"], [])
    expansion = SECTION_DATA_EXPANSION.get(section["file"], [])
    supplemental = SECTION_SUPPLEMENTAL_CHARTS.get(section["file"], [])
    front_context = SECTION_FRONT_CONTEXT.get(section["file"], {})
    independent = SECTION_INDEPENDENT_ANALYSIS.get(section["file"], {})
    analysis_html = ""
    if narrative:
        paragraphs = "\n".join(f"<p>{esc(p)}</p>" for p in narrative["paragraphs"])
        analysis_html = f"""<section class="book-narrative">
  <p class="kicker">{esc(narrative["kicker"])}</p>
  {paragraphs}
</section>"""
    elif analysis:
        paragraphs = "\n".join(f"<p>{esc(p)}</p>" for p in analysis["paragraphs"])
        analysis_html = f"""<section class="panel analysis-panel">
  <h2>{esc(analysis["heading"])}</h2>
  {paragraphs}
</section>"""
    reading_html = ""
    if reading_note:
        reading_paragraphs = "\n".join(f"<p>{esc(p)}</p>" for p in reading_note)
        reading_html = f"""<div class="reading-note">
  {reading_paragraphs}
</div>"""
    supplemental_html = ""
    if supplemental:
        cards = []
        for chart_id in supplemental:
            chart_meta = CHART_META[chart_id]
            csv_href_extra = f"../data/derived/{chart_meta['csv']}"
            cards.append(
                f"""<article class="supplement-chart">
  <div class="chart-panel-header">
    <h3>{esc(chart_meta["title"])}</h3>
    <a class="csv-button" href="{csv_href_extra}" download>CSV 다운로드</a>
  </div>
  <div class="chart-box book-chart small-book-chart"><canvas data-book-chart="{chart_id}"></canvas></div>
  <div class="chart-actions source-actions">
    <span>출처: {esc(chart_meta["source"])}</span>
  </div>
  <p class="source-note">{esc(chart_meta["note"])}</p>
</article>"""
            )
        supplemental_html = f"""<section class="panel supplemental-panel">
  <div class="supplement-grid">{''.join(cards)}</div>
</section>"""
    front_context_html = ""
    if front_context:
        front_chart = CHART_META[front_context["chart"]]
        front_paragraphs = "\n".join(f"<p>{esc(p)}</p>" for p in front_context["paragraphs"])
        front_csv = f"../data/derived/{front_chart['csv']}"
        front_context_html = f"""<section class="panel front-context-panel">
  <div class="chart-panel-header">
    <h2>{esc(front_context["heading"])}</h2>
    <a class="csv-button" href="{front_csv}" download>CSV 다운로드</a>
  </div>
  <div class="book-narrative regional-analysis-copy">
    {front_paragraphs}
  </div>
  <div class="chart-box book-chart"><canvas data-book-chart="{front_context["chart"]}"></canvas></div>
  <div class="chart-actions source-actions">
    <span>출처: {esc(front_chart["source"])}</span>
  </div>
  <p class="source-note">{esc(front_chart["note"])}</p>
</section>"""
    independent_html = ""
    if independent:
        independent_chart = CHART_META[independent["chart"]]
        independent_paragraphs = "\n".join(f"<p>{esc(p)}</p>" for p in independent["paragraphs"])
        independent_csv = f"../data/derived/{independent_chart['csv']}"
        independent_html = f"""<section class="panel independent-analysis-panel">
  <div class="chart-panel-header">
    <h2>{esc(independent["heading"])}</h2>
    <a class="csv-button" href="{independent_csv}" download>CSV 다운로드</a>
  </div>
  <div class="book-narrative regional-analysis-copy">
    {independent_paragraphs}
  </div>
  <div class="chart-box book-chart"><canvas data-book-chart="{independent["chart"]}"></canvas></div>
  <div class="chart-actions source-actions">
    <span>출처: {esc(independent_chart["source"])}</span>
  </div>
  <p class="source-note">{esc(independent_chart["note"])}</p>
</section>"""
    ending_table_html = ""
    if section["file"] == "section-5-4-aging-budget.html":
        ending_table_html = aging_budget_program_table_html()
    csv_href = f"../data/derived/{meta['csv']}"
    return f"""<section class="section-header-block">
  <p class="series">Chapter {chapter["no"]}</p>
  <h1>{section["no"]}. {esc(section["title"])}</h1>
  <p class="lead">{esc(chapter["thesis"])}</p>
  {page_feedback_link(section["no"], section["title"], section["file"])}
</section>
{analysis_html}
{front_context_html}
<section class="panel">
  <div class="chart-panel-header">
    <h2>{esc(meta["title"])}</h2>
    <a class="csv-button" href="{csv_href}" download>CSV 다운로드</a>
  </div>
  <div class="chart-box book-chart"><canvas data-book-chart="{section["chart"]}"></canvas></div>
  <div class="chart-actions source-actions">
    <span>출처: {esc(meta["source"])}</span>
  </div>
  <p class="source-note">{esc(meta["note"])}</p>
  {reading_html}
</section>
{supplemental_html}
{independent_html}
{ending_table_html}"""


def appendix_body() -> str:
    groups = []
    for chapter in BOOK:
        section_blocks = []
        for section in chapter["sections"]:
            expansion = SECTION_DATA_EXPANSION.get(section["file"], [])
            if not expansion:
                continue
            rows = []
            for item in expansion:
                file_links = " ".join(
                    f'<a class="csv-button evidence-link" href="../{esc(path)}" download>{esc(Path(path).name)}</a>'
                    for path in item["files"]
                )
                rows.append(
                    f"""<article class="evidence-item">
  <h4>{esc(item["question"])}</h4>
  <dl>
    <div><dt>활용 자료</dt><dd>{esc(item["data"])}</dd></div>
    <div><dt>자료 파일</dt><dd class="evidence-files">{file_links}</dd></div>
    <div><dt>분석</dt><dd>{esc(item["analysis"])}</dd></div>
    <div><dt>해석</dt><dd>{esc(item["interpretation"])}</dd></div>
  </dl>
</article>"""
                )
            section_blocks.append(
                f"""<section class="appendix-section">
  <h3>{section["no"]}. {esc(section["title"])}</h3>
  <div class="evidence-grid">{''.join(rows)}</div>
</section>"""
            )
        if section_blocks:
            groups.append(
                f"""<section class="panel appendix-chapter">
  <h2>{chapter["no"]}. {esc(chapter["title"])}</h2>
  {''.join(section_blocks)}
</section>"""
            )
    narrative = """<section id="book-narrative" class="section narrative-flow">
  <h2>책의 서사</h2>
  <p>핵심 논리는 단순합니다. 출산율이 낮아졌다는 사실에서 출발하되, 곧바로 “출산율을 어떻게 올릴 것인가”로 뛰지 않습니다. 먼저 지표가 무엇을 말하고 무엇을 숨기는지 확인하고, 이어서 출생 코호트가 실제 지역 안에 남는지, 청년과 가족이 이동하는지, 가구와 노동시장과 재정이 어떤 압력을 받는지 추적합니다.</p>
  <div class="flow-steps" aria-label="책의 논리 흐름">
    <article>
      <span>1</span>
      <h3>지표의 함정</h3>
      <p>합계출산율, 출생아 수, 주민등록인구, 연앙인구, 인구총조사는 서로 다른 현실을 잽니다.</p>
    </article>
    <article>
      <span>2</span>
      <h3>정책 점검</h3>
      <p>높은 출산율이 실제 유아 인구 유지와 정주 조건 개선으로 이어지는지 사례와 전국 지표를 함께 확인합니다.</p>
    </article>
    <article>
      <span>3</span>
      <h3>구조 변화</h3>
      <p>20-30대 감소, 초등학생 감소, 고령화율, 부양비를 통해 인구구조의 방향을 읽습니다.</p>
    </article>
    <article>
      <span>4</span>
      <h3>지역 격차</h3>
      <p>전국 평균 뒤에 숨은 시군구별 속도 차이를 GIS와 지역 패널로 드러냅니다.</p>
    </article>
    <article>
      <span>5</span>
      <h3>생활시간표</h3>
      <p>가구 형성, 주거, 혼인, 육아휴직, 보육이 출산 결정의 시간표를 어떻게 앞당기거나 늦추는지 봅니다.</p>
    </article>
    <article>
      <span>6</span>
      <h3>노동과 재정</h3>
      <p>고령층 경제활동, 인력부족, 생애주기 적자, 보건·돌봄 지출로 결론을 확장합니다.</p>
    </article>
  </div>
  <div class="thesis-box">
    <strong>이 책의 중심 질문</strong>
    <p>한국은 왜 아이를 적게 낳는가에서 끝나지 않고, 어떤 지역과 어떤 세대가 먼저 줄어들며, 누가 남아 돌봄과 노동과 재정을 감당하게 되는가를 묻습니다.</p>
  </div>
</section>"""
    return f"""<section class="section-header-block">
  <p class="series">Appendix</p>
  <h1>부록. 자료와 분석 설계</h1>
  <p class="lead">본문의 흐름을 끊지 않기 위해 책의 서사, 각 절의 자료 경로, 분석 방식, 해석상의 주의점을 한곳에 모았다.</p>
</section>
{narrative}
{''.join(groups)}"""


def chapter_body(chapter: dict) -> str:
    manuscript = chapter_manuscript_path(chapter)
    if manuscript.exists():
        body = render_markdown(manuscript.read_text(encoding="utf-8"), rel="..")
        return f"""<section class="section-header-block">
  <p class="series">Chapter {chapter["no"]}</p>
  <h1>{chapter["no"]}. {esc(chapter["title"])}</h1>
  <p class="lead">{esc(chapter["thesis"])}</p>
  {page_feedback_link(chapter["no"], chapter["title"], chapter["file"])}
</section>
<div class="markdown-manuscript chapter-manuscript">
{body}
</div>"""
    cards = []
    for section in chapter["sections"]:
        meta = CHART_META[section["chart"]]
        cards.append(
            f"""<a class="chapter-card" href="../sections/{section["file"]}">
  <span>{section["no"]}</span>
  <h2>{esc(section["title"])}</h2>
  <p>{esc(meta["note"])}</p>
</a>"""
        )
    prose = "\n".join(f"<p>{esc(paragraph)}</p>" for paragraph in CHAPTER_NARRATIVE.get(chapter["file"], []))
    cards_html = f'\n<section class="chapter-grid">{"".join(cards)}</section>' if cards else ""
    return f"""<section class="section-header-block">
  <p class="series">Chapter {chapter["no"]}</p>
  <h1>{chapter["no"]}. {esc(chapter["title"])}</h1>
  <p class="lead">{esc(chapter["thesis"])}</p>
  {page_feedback_link(chapter["no"], chapter["title"], chapter["file"])}
</section>
<section class="book-narrative chapter-opening">
  {prose}
</section>{cards_html}"""


def write_pages() -> None:
    CHAPTERS.mkdir(exist_ok=True)
    SECTIONS.mkdir(exist_ok=True)
    for chapter in BOOK:
        (CHAPTERS / chapter["file"]).write_text(
            shell(f'{chapter["no"]}. {chapter["title"]}', chapter_body(chapter), chapter["file"]),
            encoding="utf-8",
        )
        for section in chapter["sections"]:
            (SECTIONS / section["file"]).write_text(
                shell(f'{section["no"]}. {section["title"]}', section_body(chapter, section), section["file"]),
                encoding="utf-8",
            )
    (SECTIONS / APPENDIX_FILE).write_text(
        shell("부록. 자료와 분석 설계", appendix_body(), APPENDIX_FILE),
        encoding="utf-8",
    )


def write_book_data(charts: dict[str, list[dict[str, object]]]) -> None:
    payload = {"charts": charts, "meta": CHART_META}
    (ROOT / "book_chart_data.js").write_text(
        "window.populationBookCharts = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    charts = build_derived_data()
    ensure_markdown_manuscripts()
    write_book_data(charts)
    write_pages()
    print(f"Built {len(BOOK)} chapter pages and {sum(len(c['sections']) for c in BOOK)} section pages.")


if __name__ == "__main__":
    main()

