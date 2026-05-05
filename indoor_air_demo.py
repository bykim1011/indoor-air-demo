# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

# indoor_air_demo.py
# ------------------------------------------------------------
# 실내공기질 안내서비스 1차 데모
# 목적:
# - PM2.5, PM10 농도 입력
# - 등급 자동 판정
# - 얼굴 아이콘 표시
# - 행동요령 안내
# - 이용자 반응 버튼
# - 반응 결과 CSV 저장
#
# 실행:
# streamlit run indoor_air_demo.py
# ------------------------------------------------------------

import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path


# ============================================================
# 1. 기본 설정
# ============================================================

KST = timezone(timedelta(hours=9))

def get_kst_now():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(
    page_title="실내공기질 안내서비스 데모",
    page_icon="🌿",
    layout="wide"
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

FEEDBACK_FILE = DATA_DIR / "user_feedback_log.csv"


# ============================================================
# 2. 등급 판정 함수
# ============================================================
# 기준은 데모용 단순 기준입니다.
# 실제 적용 시에는 환경부/에어코리아 기준, 실내공기질 관리 기준,
# 측정기 보정 기준 등을 검토해 조정하는 것이 좋습니다.

def get_pm25_grade(pm25):
    """
    PM2.5 농도 기준 등급 판정
    단위: µg/m³
    """
    if pm25 <= 15:
        return "좋음"
    elif pm25 <= 35:
        return "보통"
    elif pm25 <= 75:
        return "나쁨"
    else:
        return "매우나쁨"


def get_pm10_grade(pm10):
    """
    PM10 농도 기준 등급 판정
    단위: µg/m³
    """
    if pm10 <= 30:
        return "좋음"
    elif pm10 <= 80:
        return "보통"
    elif pm10 <= 150:
        return "나쁨"
    else:
        return "매우나쁨"


def get_final_grade(pm25_grade, pm10_grade):
    """
    PM2.5와 PM10 중 더 나쁜 등급을 최종 등급으로 사용
    """
    grade_order = {
        "좋음": 1,
        "보통": 2,
        "나쁨": 3,
        "매우나쁨": 4
    }

    if grade_order[pm25_grade] >= grade_order[pm10_grade]:
        return pm25_grade
    else:
        return pm10_grade


def get_face_icon(grade):
    """
    등급별 얼굴 아이콘
    """
    icons = {
        "좋음": "😊",
        "보통": "🙂",
        "나쁨": "😷",
        "매우나쁨": "🤢"
    }
    return icons.get(grade, "🙂")


def get_action_message(grade):
    """
    등급별 행동요령 문구
    """
    messages = {
        "좋음": "실내공기질이 양호합니다. 현재 상태를 유지해 주세요.",
        "보통": "대체로 무난한 상태입니다. 민감군은 장시간 노출을 주의해 주세요.",
        "나쁨": "공기질이 좋지 않습니다. 환기 여부를 확인하고, 공기청정기 가동을 권장합니다.",
        "매우나쁨": "공기질이 매우 나쁩니다. 실내 활동을 조정하고, 즉시 환기 또는 공기정화 조치가 필요합니다."
    }
    return messages.get(grade, "상태를 확인해 주세요.")


def get_grade_color(grade):
    """
    등급별 표시 색상
    """
    colors = {
        "좋음": "#2E86DE",
        "보통": "#27AE60",
        "나쁨": "#F39C12",
        "매우나쁨": "#C0392B"
    }
    return colors.get(grade, "#7F8C8D")


# ============================================================
# 3. 이용자 반응 저장 함수
# ============================================================

def save_feedback(feedback, pm25, pm10, temp, humidity, final_grade):
    """
    이용자 반응을 CSV 파일에 누적 저장
    """
    now = get_kst_now()
    
    new_row = pd.DataFrame([{
        "datetime": now,
        "feedback": feedback,
        "pm25": pm25,
        "pm10": pm10,
        "temperature": temp,
        "humidity": humidity,
        "final_grade": final_grade
    }])

    if FEEDBACK_FILE.exists():
        old_df = pd.read_csv(FEEDBACK_FILE, encoding="utf-8-sig")
        result_df = pd.concat([old_df, new_row], ignore_index=True)
    else:
        result_df = new_row

    result_df.to_csv(FEEDBACK_FILE, index=False, encoding="utf-8-sig")


def load_feedback_summary():
    """
    저장된 이용자 반응 CSV를 읽어 간단 집계
    """
    if FEEDBACK_FILE.exists():
        df = pd.read_csv(FEEDBACK_FILE, encoding="utf-8-sig")
        summary = df["feedback"].value_counts().reset_index()
        summary.columns = ["반응", "건수"]
        return df, summary
    else:
        return pd.DataFrame(), pd.DataFrame(columns=["반응", "건수"])


# ============================================================
# 4. 화면 제목
# ============================================================

st.title("🌿 실내공기질 안내서비스 데모")
st.caption("미세먼지 간이측정기 자료를 활용한 실내공기질 안내 화면 예시")
st.caption(f"현재 표시 시간: {get_kst_now()} KST")
st.markdown("---")


# ============================================================
# 5. 사이드바 입력부
# ============================================================

st.sidebar.header("측정값 입력")

input_mode = st.sidebar.radio(
    "입력 방식 선택",
    ["슬라이더 입력", "직접 숫자 입력"]
)

if input_mode == "슬라이더 입력":
    pm25 = st.sidebar.slider("PM2.5 농도 (µg/m³)", 0, 150, 22)
    pm10 = st.sidebar.slider("PM10 농도 (µg/m³)", 0, 250, 45)
    temp = st.sidebar.slider("실내 온도 (℃)", 0.0, 40.0, 24.5, 0.1)
    humidity = st.sidebar.slider("실내 습도 (%)", 0.0, 100.0, 55.0, 0.1)

else:
    pm25 = st.sidebar.number_input("PM2.5 농도 (µg/m³)", min_value=0.0, max_value=500.0, value=22.0, step=1.0)
    pm10 = st.sidebar.number_input("PM10 농도 (µg/m³)", min_value=0.0, max_value=500.0, value=45.0, step=1.0)
    temp = st.sidebar.number_input("실내 온도 (℃)", min_value=-20.0, max_value=60.0, value=24.5, step=0.1)
    humidity = st.sidebar.number_input("실내 습도 (%)", min_value=0.0, max_value=100.0, value=55.0, step=0.1)


# ============================================================
# 6. 등급 계산
# ============================================================

pm25_grade = get_pm25_grade(pm25)
pm10_grade = get_pm10_grade(pm10)
final_grade = get_final_grade(pm25_grade, pm10_grade)
face_icon = get_face_icon(final_grade)
action_message = get_action_message(final_grade)
grade_color = get_grade_color(final_grade)


# ============================================================
# 7. 메인 화면 구성
# ============================================================

left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.subheader("현재 실내공기질 상태")

    st.markdown(
        f"""
        <div style="
            background-color:{grade_color};
            padding:30px;
            border-radius:20px;
            text-align:center;
            color:white;
            margin-bottom:20px;
        ">
            <div style="font-size:90px;">{face_icon}</div>
            <div style="font-size:42px; font-weight:bold;">{final_grade}</div>
            <div style="font-size:18px; margin-top:10px;">현재 실내공기질 종합 상태</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(action_message)

with right_col:
    st.subheader("측정값")

    metric_col1, metric_col2 = st.columns(2)

    with metric_col1:
        st.metric("PM2.5", f"{pm25:.1f} µg/m³")
        st.markdown(f"**등급:** {pm25_grade}")
        st.metric("온도", f"{temp:.1f} ℃")

    with metric_col2:
        st.metric("PM10", f"{pm10:.1f} µg/m³")
        st.markdown(f"**등급:** {pm10_grade}")
        st.metric("습도", f"{humidity:.1f} %")


st.markdown("---")


# ============================================================
# 8. 등급별 세부 안내
# ============================================================

st.subheader("등급별 해석")

grade_table = pd.DataFrame({
    "구분": ["좋음", "보통", "나쁨", "매우나쁨"],
    "얼굴": ["😊", "🙂", "😷", "🤢"],
    "안내 문구": [
        "현재 상태 유지",
        "민감군 주의",
        "환기 및 공기청정기 가동 권장",
        "즉시 조치 필요"
    ]
})

st.dataframe(grade_table, use_container_width=True, hide_index=True)


# ============================================================
# 9. 이용자 반응 버튼
# ============================================================

st.subheader("이용자 반응")

st.write("현재 실내공기질 안내가 체감과 맞나요?")

btn_col1, btn_col2, btn_col3 = st.columns(3)

with btn_col1:
    if st.button("👍 좋아요", use_container_width=True):
        save_feedback("좋아요", pm25, pm10, temp, humidity, final_grade)
        st.success("반응이 저장되었습니다: 좋아요")

with btn_col2:
    if st.button("😐 보통이에요", use_container_width=True):
        save_feedback("보통이에요", pm25, pm10, temp, humidity, final_grade)
        st.success("반응이 저장되었습니다: 보통이에요")

with btn_col3:
    if st.button("🙁 불편해요", use_container_width=True):
        save_feedback("불편해요", pm25, pm10, temp, humidity, final_grade)
        st.warning("반응이 저장되었습니다: 불편해요")


# ============================================================
# 10. 반응 결과 집계
# ============================================================

st.markdown("---")
st.subheader("이용자 반응 누적 결과")

feedback_df, feedback_summary = load_feedback_summary()

if len(feedback_df) == 0:
    st.write("아직 저장된 이용자 반응이 없습니다.")
else:
    sum_col1, sum_col2 = st.columns([1, 2])

    with sum_col1:
        st.write("반응 집계")
        st.dataframe(feedback_summary, use_container_width=True, hide_index=True)

    with sum_col2:
        st.write("최근 반응 기록")
        st.dataframe(
            feedback_df.tail(10).sort_values("datetime", ascending=False),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# 11. 향후 확장 안내
# ============================================================

st.markdown("---")
st.subheader("향후 확장 가능 구조")

st.markdown("""
현재 데모는 수동 입력 방식이지만, 이후에는 다음과 같이 확장할 수 있습니다.

- 간이측정기 CSV 파일 자동 불러오기
- 실시간 센서 API 연동
- AirKorea 외부 대기질 자료 연동
- 기상자료 연동
- 시설별 화면 분리
- 시간대별 공기질 변화 그래프 추가
- 이용자 반응과 실제 농도 조건 비교
- 어린이집, 노인복지시설, 다중이용시설별 맞춤 행동요령 제공
""")

st.caption("※ 본 화면은 정책·사업 기획 검토용 1차 데모이며, 실제 서비스 적용 전에는 측정기 보정, 기준 설정, 안내문 검토가 필요합니다.")
