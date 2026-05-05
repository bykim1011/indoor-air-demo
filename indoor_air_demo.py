# indoor_air_demo.py
# ------------------------------------------------------------
# 실내공기질 안내서비스 1차 웹 데모
#
# 기능:
# 1. 수동 입력 모드
# 2. AirKorea CSV 조회 모드
# 3. PM2.5 / PM10 기준 등급 판정
# 4. 얼굴 아이콘 및 행동요령 표시
# 5. O3, NO2, SO2, CO 참고 표시
# 6. 이용자 반응 저장
# ------------------------------------------------------------

import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from pathlib import Path


# ============================================================
# 1. 기본 설정
# ============================================================

st.set_page_config(
    page_title="실내공기질 안내서비스 데모",
    page_icon="🌿",
    layout="wide"
)

KST = timezone(timedelta(hours=9))

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

FEEDBACK_FILE = DATA_DIR / "user_feedback_log.csv"

AIRKOREA_CSV = Path("sample_airkorea_pyeongri_202604_clean.csv")


def get_kst_now():
    return datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# 2. 표시용 함수
# ============================================================

def format_value(value, unit):
    """
    NaN이면 자료없음으로 표시
    """
    if pd.isna(value):
        return "자료없음"
    return f"{value:.1f} {unit}"


def format_ppm(value):
    """
    ppm 항목 표시용
    """
    if pd.isna(value):
        return "자료없음"
    return f"{value:.4f} ppm"


# ============================================================
# 3. 등급 판정 함수
# ============================================================

def get_pm25_grade(pm25):
    """
    PM2.5 농도 기준 등급 판정
    단위: µg/m³
    """
    if pd.isna(pm25):
        return "자료없음"

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
    if pd.isna(pm10):
        return "자료없음"

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
    단, 둘 중 하나가 자료없음이면 있는 값 기준으로 판정
    둘 다 자료없음이면 최종 등급도 자료없음
    """
    grade_order = {
        "좋음": 1,
        "보통": 2,
        "나쁨": 3,
        "매우나쁨": 4
    }

    valid_grades = []

    if pm25_grade in grade_order:
        valid_grades.append(pm25_grade)

    if pm10_grade in grade_order:
        valid_grades.append(pm10_grade)

    if len(valid_grades) == 0:
        return "자료없음"

    return max(valid_grades, key=lambda x: grade_order[x])


def get_face_icon(grade):
    icons = {
        "좋음": "😊",
        "보통": "🙂",
        "나쁨": "😷",
        "매우나쁨": "🤢",
        "자료없음": "❔"
    }
    return icons.get(grade, "❔")


def get_action_message(grade, mode):
    """
    등급별 행동요령 문구
    mode에 따라 문구를 약간 다르게 표시
    """
    if mode == "AirKorea CSV 조회":
        messages = {
            "좋음": "외부 대기질이 양호한 편입니다. 실제 실내 적용 시에는 실내 센서값과 함께 판단할 수 있습니다.",
            "보통": "외부 대기질은 대체로 보통 수준입니다. 민감군은 장시간 노출을 주의해 주세요.",
            "나쁨": "외부 미세먼지 농도가 높은 편입니다. 실내 환기 여부는 실내 농도와 함께 판단하는 것이 좋습니다.",
            "매우나쁨": "외부 미세먼지 농도가 매우 높습니다. 창문 개방이나 실외활동 안내에 주의가 필요합니다.",
            "자료없음": "해당 시각의 PM2.5 또는 PM10 측정값이 없어 등급을 판정할 수 없습니다."
        }
    else:
        messages = {
            "좋음": "실내공기질이 양호합니다. 현재 상태를 유지해 주세요.",
            "보통": "대체로 무난한 상태입니다. 민감군은 장시간 노출을 주의해 주세요.",
            "나쁨": "공기질이 좋지 않습니다. 환기 여부를 확인하고, 공기청정기 가동을 권장합니다.",
            "매우나쁨": "공기질이 매우 나쁩니다. 실내 활동을 조정하고, 즉시 환기 또는 공기정화 조치가 필요합니다.",
            "자료없음": "해당 시각의 측정값이 없어 등급을 판정할 수 없습니다."
        }

    return messages.get(grade, "상태를 확인해 주세요.")


def get_grade_color(grade):
    colors = {
        "좋음": "#2E86DE",
        "보통": "#27AE60",
        "나쁨": "#F39C12",
        "매우나쁨": "#C0392B",
        "자료없음": "#7F8C8D"
    }
    return colors.get(grade, "#7F8C8D")


# ============================================================
# 4. 이용자 반응 저장 함수
# ============================================================

def save_feedback(feedback, pm25, pm10, final_grade, data_mode, selected_time=None, station=None):
    """
    이용자 반응을 CSV 파일에 누적 저장
    """
    now = get_kst_now()

    new_row = pd.DataFrame([{
        "feedback_time_kst": now,
        "feedback": feedback,
        "data_mode": data_mode,
        "selected_time": selected_time,
        "station": station,
        "pm25": pm25,
        "pm10": pm10,
        "final_grade": final_grade
    }])

    if FEEDBACK_FILE.exists():
        old_df = pd.read_csv(FEEDBACK_FILE, encoding="utf-8-sig")
        result_df = pd.concat([old_df, new_row], ignore_index=True)
    else:
        result_df = new_row

    result_df.to_csv(FEEDBACK_FILE, index=False, encoding="utf-8-sig")


def load_feedback_summary():
    if FEEDBACK_FILE.exists():
        df = pd.read_csv(FEEDBACK_FILE, encoding="utf-8-sig")
        if "feedback" in df.columns:
            summary = df["feedback"].value_counts().reset_index()
            summary.columns = ["반응", "건수"]
            return df, summary

    return pd.DataFrame(), pd.DataFrame(columns=["반응", "건수"])


# ============================================================
# 5. AirKorea CSV 읽기 함수
# ============================================================

@st.cache_data
def load_airkorea_csv():
    df = pd.read_csv(AIRKOREA_CSV, encoding="utf-8-sig")
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df


# ============================================================
# 6. 화면 제목
# ============================================================

st.title("🌿 실내공기질 안내서비스 데모")
st.caption("미세먼지 간이측정기 자료를 활용한 실내공기질 안내 화면 예시")
st.caption(f"현재 표시 기준: {get_kst_now()} (한국시간)")

st.markdown("---")


# ============================================================
# 7. 입력 방식 선택
# ============================================================

st.sidebar.header("자료 입력 방식")

data_mode = st.sidebar.radio(
    "입력 방식 선택",
    ["수동 입력", "AirKorea CSV 조회"]
)


# ============================================================
# 8. 수동 입력 모드
# ============================================================

selected_time = None
station = None
o3 = None
no2 = None
co = None
so2 = None
temp = None
humidity = None

if data_mode == "수동 입력":

    st.sidebar.subheader("수동 측정값 입력")

    input_mode = st.sidebar.radio(
        "수동 입력 방식",
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
# 9. AirKorea CSV 조회 모드
# ============================================================

else:
    st.sidebar.subheader("AirKorea CSV 조회")

    if not AIRKOREA_CSV.exists():
        st.error(f"CSV 파일이 없습니다: {AIRKOREA_CSV}")
        st.stop()

    air_df = load_airkorea_csv()

    station = air_df["station"].dropna().iloc[0] if "station" in air_df.columns else "측정소명 없음"

    available_dates = sorted(air_df["datetime"].dt.date.unique())
    
    min_date = min(available_dates)
    max_date = max(available_dates)
    
    selected_date = st.sidebar.date_input(
        "조회 날짜 선택",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )
    
    day_df = air_df[air_df["datetime"].dt.date == selected_date].copy()
    
    if len(day_df) == 0:
        st.warning("선택한 날짜의 자료가 없습니다.")
        st.stop()

    available_times = sorted(day_df["datetime"].dt.strftime("%H:%M").unique())

    selected_time_str = st.sidebar.selectbox(
        "조회 시간 선택",
        available_times,
        index=0
    )

    selected_datetime = pd.to_datetime(f"{selected_date} {selected_time_str}")

    selected_row = air_df[air_df["datetime"] == selected_datetime]

    if len(selected_row) == 0:
        st.warning("선택한 시각의 자료가 없습니다.")
        st.stop()

    row = selected_row.iloc[0]

    selected_time = selected_datetime.strftime("%Y-%m-%d %H:%M:%S")

    pm25 = row.get("pm25", pd.NA)
    pm10 = row.get("pm10", pd.NA)
    o3 = row.get("o3", pd.NA)
    no2 = row.get("no2", pd.NA)
    co = row.get("co", pd.NA)
    so2 = row.get("so2", pd.NA)


# ============================================================
# 10. 등급 계산
# ============================================================

pm25_grade = get_pm25_grade(pm25)
pm10_grade = get_pm10_grade(pm10)
final_grade = get_final_grade(pm25_grade, pm10_grade)

face_icon = get_face_icon(final_grade)
action_message = get_action_message(final_grade, data_mode)
grade_color = get_grade_color(final_grade)


# ============================================================
# 11. 메인 화면 구성
# ============================================================

left_col, right_col = st.columns([1.2, 1])

with left_col:
    if data_mode == "수동 입력":
        st.subheader("현재 실내공기질 상태")
    else:
        st.subheader("선택 시각 대기질 상태")

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
            <div style="font-size:18px; margin-top:10px;">PM2.5 / PM10 기준 종합 상태</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(action_message)

    if data_mode == "AirKorea CSV 조회":
        st.caption("※ 현재 CSV 조회 모드는 실내 간이측정기 자료가 확보되기 전, AirKorea 자료를 예시로 사용한 화면입니다.")

with right_col:
    st.subheader("측정값")

    if data_mode == "AirKorea CSV 조회":
        st.write(f"**측정소:** {station}")
        st.write(f"**조회 시각:** {selected_time}")

    metric_col1, metric_col2 = st.columns(2)

    with metric_col1:
        st.metric("PM2.5", format_value(pm25, "µg/m³"))
        st.markdown(f"**등급:** {pm25_grade}")

        if data_mode == "수동 입력":
            st.metric("온도", format_value(temp, "℃"))
        else:
            st.metric("O3", format_ppm(o3))
            st.metric("NO2", format_ppm(no2))

    with metric_col2:
        st.metric("PM10", format_value(pm10, "µg/m³"))
        st.markdown(f"**등급:** {pm10_grade}")

        if data_mode == "수동 입력":
            st.metric("습도", format_value(humidity, "%"))
        else:
            st.metric("CO", format_ppm(co))
            st.metric("SO2", format_ppm(so2))


# ============================================================
# 12. AirKorea 1일 변화 그래프
# ============================================================

if data_mode == "AirKorea CSV 조회":
    st.markdown("---")
    st.subheader("선택 날짜의 미세먼지 변화")

    plot_df = day_df[["datetime", "pm25", "pm10"]].copy()
    plot_df = plot_df.set_index("datetime")

    st.line_chart(plot_df)

    st.caption("※ 빈칸 또는 장비 오류로 인한 결측값은 그래프에서 끊겨 보일 수 있습니다.")


# ============================================================
# 13. 등급별 해석표
# ============================================================

st.markdown("---")
st.subheader("등급별 해석")

grade_table = pd.DataFrame({
    "구분": ["좋음", "보통", "나쁨", "매우나쁨", "자료없음"],
    "얼굴": ["😊", "🙂", "😷", "🤢", "❔"],
    "안내 문구": [
        "현재 상태 유지",
        "민감군 주의",
        "환기 또는 활동관리 검토",
        "즉시 조치 필요",
        "측정값 없음"
    ]
})

st.dataframe(grade_table, use_container_width=True, hide_index=True)


# ============================================================
# 14. 이용자 반응 버튼
# ============================================================

st.markdown("---")
st.subheader("이용자 반응")

st.write("현재 안내가 체감과 맞나요?")

btn_col1, btn_col2, btn_col3 = st.columns(3)

with btn_col1:
    if st.button("👍 좋아요", use_container_width=True):
        save_feedback("좋아요", pm25, pm10, final_grade, data_mode, selected_time, station)
        st.success("반응이 저장되었습니다: 좋아요")

with btn_col2:
    if st.button("😐 보통이에요", use_container_width=True):
        save_feedback("보통이에요", pm25, pm10, final_grade, data_mode, selected_time, station)
        st.success("반응이 저장되었습니다: 보통이에요")

with btn_col3:
    if st.button("🙁 불편해요", use_container_width=True):
        save_feedback("불편해요", pm25, pm10, final_grade, data_mode, selected_time, station)
        st.warning("반응이 저장되었습니다: 불편해요")


# ============================================================
# 15. 반응 결과 집계
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

        # 기존 버전에서는 시간 컬럼명이 datetime이었고,
        # 새 버전에서는 feedback_time_kst로 저장되므로 둘 다 대응
        if "feedback_time_kst" in feedback_df.columns:
            sort_col = "feedback_time_kst"
        elif "datetime" in feedback_df.columns:
            sort_col = "datetime"
        else:
            sort_col = None

        if sort_col is not None:
            recent_df = feedback_df.tail(10).sort_values(sort_col, ascending=False)
        else:
            recent_df = feedback_df.tail(10)

        st.dataframe(
            recent_df,
            use_container_width=True,
            hide_index=True
        )
        
# ============================================================
# 16. 안내 문구
# ============================================================

st.markdown("---")
st.subheader("향후 확장 가능 구조")

st.markdown("""
현재 데모는 수동 입력과 AirKorea CSV 조회를 함께 지원합니다.

- 수동 입력 모드: 실내 간이측정기 값이 들어온 상황을 가정한 화면
- AirKorea CSV 조회 모드: 실제 시간자료 CSV를 불러와 특정 시각의 농도를 조회하는 화면
- 향후 실제 실내 간이측정기 CSV로 교체하면 동일한 구조로 실내공기질 안내 화면을 구성할 수 있음
- 기상청 AWS 자료를 추가하면 온도, 습도, 풍속, 풍향을 함께 표시 가능
- AirKorea 또는 기상청 API를 연동하면 실시간 자동 조회형 서비스로 확장 가능
""")

st.caption("※ 본 화면은 정책·사업 기획 검토용 1차 데모이며, 실제 서비스 적용 전에는 측정기 보정, 기준 설정, 안내문 검토가 필요합니다.")
