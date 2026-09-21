import streamlit as st
import requests
from datetime import datetime, timedelta, timezone


# --------------------------------------------------
# 1. 페이지 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="KOBIS 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 KOBIS 일일 박스오피스")


# --------------------------------------------------
# 2. 한국 시간 기준 날짜 계산
# --------------------------------------------------

# 배포 서버의 시간이 한국 시간이 아닐 수 있으므로
# UTC+9를 사용해서 한국 시간을 직접 계산합니다.
KST = timezone(timedelta(hours=9))

today_kst = datetime.now(KST).date()

# 오늘 영화 데이터는 아직 집계 전이므로
# 선택할 수 있는 가장 늦은 날짜를 어제로 설정합니다.
yesterday = today_kst - timedelta(days=1)


# --------------------------------------------------
# 3. 조회 날짜 선택
# --------------------------------------------------

st.subheader("📅 조회할 날짜")

selected_date = st.date_input(
    "날짜를 선택하세요.",
    value=yesterday,
    max_value=yesterday,
    format="YYYY-MM-DD"
)

# KOBIS API가 요구하는 YYYYMMDD 형식으로 변환합니다.
target_dt = selected_date.strftime("%Y%m%d")

st.caption(
    f"선택한 날짜: {selected_date.strftime('%Y년 %m월 %d일')}"
)


# --------------------------------------------------
# 4. KOBIS API에서 데이터 가져오기
# --------------------------------------------------

# 같은 날짜를 다시 조회하면 약 1시간 동안
# 저장된 결과를 사용합니다.
@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):

    # 인증키는 Streamlit Secrets에서 가져옵니다.
    api_key = st.secrets["KOBIS_KEY"]

    url = (
        "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
        "boxoffice/searchDailyBoxOfficeList.json"
    )

    params = {
        "key": api_key,
        "targetDt": target_dt
    }

    try:
        # KOBIS API에 요청합니다.
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        # JSON 형태로 응답을 받습니다.
        data = response.json()

    except requests.exceptions.RequestException as e:
        return None, f"API 요청에 실패했습니다: {e}"

    except ValueError:
        return None, "API 응답을 JSON으로 읽을 수 없습니다."

    # --------------------------------------------------
    # 5. KOBIS의 faultInfo 확인
    # --------------------------------------------------

    # 인증키가 잘못되어도 HTTP 상태코드는 200일 수 있으므로
    # faultInfo가 있는지 따로 확인합니다.
    if "faultInfo" in data:

        fault = data["faultInfo"]

        message = fault.get(
            "message",
            "알 수 없는 KOBIS API 오류"
        )

        return None, f"KOBIS API 오류: {message}"

    # --------------------------------------------------
    # 6. 영화 목록 확인
    # --------------------------------------------------

    boxoffice_result = data.get("boxOfficeResult")

    if not boxoffice_result:
        return None, "boxOfficeResult가 응답에 없습니다."

    movie_list = boxoffice_result.get(
        "dailyBoxOfficeList",
        []
    )

    # 영화 목록이 비어 있는 경우
    if not movie_list:
        return None, "NO_DATA"

    # --------------------------------------------------
    # 7. 문자열로 온 숫자를 정수로 변환
    # --------------------------------------------------

    for movie in movie_list:

        movie["rank"] = int(movie.get("rank", 0))
        movie["rankInten"] = int(
            movie.get("rankInten", 0)
        )
        movie["audiCnt"] = int(
            movie.get("audiCnt", 0)
        )
        movie["audiAcc"] = int(
            movie.get("audiAcc", 0)
        )
        movie["scrnCnt"] = int(
            movie.get("scrnCnt", 0)
        )
        movie["showCnt"] = int(
            movie.get("showCnt", 0)
        )

    # 순위순으로 정렬합니다.
    movie_list.sort(
        key=lambda movie: movie["rank"]
    )

    return movie_list, None


# --------------------------------------------------
# 8. API 호출
# --------------------------------------------------

movies, error_message = get_boxoffice(target_dt)


# --------------------------------------------------
# 9. 오류 처리
# --------------------------------------------------

if error_message:

    # 영화 목록이 없는 경우
    if error_message == "NO_DATA":

        st.warning(
            "📭 그날은 아직 집계 전입니다."
        )

        st.info(
            "다른 날짜를 선택해 주세요. "
            "KOBIS에서 해당 날짜의 일일 박스오피스 "
            "자료가 아직 제공되지 않았을 수 있습니다."
        )

    # 그 외 API 오류
    else:

        st.error(
            "박스오피스 정보를 불러오지 못했습니다."
        )

        st.warning(
            "다음 항목을 확인해 주세요.\n\n"
            "• Streamlit Secrets에 `KOBIS_KEY`가 "
            "정확히 등록되어 있는지 확인\n"
            "• KOBIS 인증키가 유효한지 확인\n"
            "• 인터넷 또는 KOBIS API 서버에 "
            "문제가 없는지 확인\n\n"
            f"상세 내용: {error_message}"
        )

    st.stop()


# --------------------------------------------------
# 10. 숫자를 보기 좋게 만드는 함수
# --------------------------------------------------

def number_format(number):
    return f"{number:,}"


# --------------------------------------------------
# 11. 1위 영화
# --------------------------------------------------

first_movie = movies[0]

st.subheader("🏆 해당 날짜의 박스오피스 1위")

st.markdown(
    f"## {first_movie['movieNm']}"
)

st.write(
    f"개봉일: {first_movie['openDt']}"
)


# --------------------------------------------------
# 12. 1위 영화의 주요 지표
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "당일 관객수",
        f"{number_format(first_movie['audiCnt'])}명"
    )

with col2:
    st.metric(
        "누적 관객수",
        f"{number_format(first_movie['audiAcc'])}명"
    )

with col3:
    st.metric(
        "스크린수",
        f"{number_format(first_movie['scrnCnt'])}개"
    )


# --------------------------------------------------
# 13. 영화명에 트로피 붙이기
# --------------------------------------------------

def movie_name_with_trophy(movie):
    """
    누적 관객수가 100만 명 이상이면
    영화명 뒤에 트로피 이모지를 붙입니다.
    """

    if movie["audiAcc"] >= 1_000_000:
        return f"{movie['movieNm']} 🏆"

    return movie["movieNm"]


# --------------------------------------------------
# 14. 순위 증감 표시
# --------------------------------------------------

def rank_change_text(movie):
    """
    rankInten은 전날과 비교한 순위 변화입니다.

    양수 → 순위 상승 → 빨간 위 화살표
    음수 → 순위 하락 → 파란 아래 화살표
    0    → 변동 없음
    """

    change = movie["rankInten"]

    if change > 0:
        return f"🔺 {change}"

    elif change < 0:
        return f"🔻 {abs(change)}"

    else:
        return "-"


# --------------------------------------------------
# 15. 전체 영화 표 만들기
# --------------------------------------------------

st.subheader("📋 일일 박스오피스")

table_data = []

for movie in movies:

    table_data.append({
        "순위": movie["rank"],
        "순위 변동": rank_change_text(movie),
        "영화명": movie_name_with_trophy(movie),
        "개봉일": movie["openDt"],
        "관객수": movie["audiCnt"],
        "누적관객": movie["audiAcc"],
        "스크린수": movie["scrnCnt"]
    })


# --------------------------------------------------
# 16. 표 출력
# --------------------------------------------------

st.dataframe(
    table_data,
    use_container_width=True,
    hide_index=True,
    column_config={

        "순위": st.column_config.NumberColumn(
            "순위"
        ),

        "순위 변동": st.column_config.TextColumn(
            "순위 변동"
        ),

        "관객수": st.column_config.NumberColumn(
            "관객수",
            format="%d명"
        ),

        "누적관객": st.column_config.NumberColumn(
            "누적관객",
            format="%d명"
        ),

        "스크린수": st.column_config.NumberColumn(
            "스크린수",
            format="%d개"
        )
    }
)


# --------------------------------------------------
# 17. 관객수 상위 5편
# --------------------------------------------------

st.subheader("📊 관객수 상위 5편")

# 관객수를 기준으로 큰 순서대로 정렬합니다.
top5 = sorted(
    movies,
    key=lambda movie: movie["audiCnt"],
    reverse=True
)[:5]


# 그래프에 사용할 데이터
chart_data = {
    movie_name_with_trophy(movie): movie["audiCnt"]
    for movie in top5
}


# 막대그래프 출력
st.bar_chart(chart_data)


# --------------------------------------------------
# 18. 데이터 출처
# --------------------------------------------------

st.caption(
    "데이터 출처: 영화관입장권통합전산망(KOBIS) "
    "일일 박스오피스 API"
)
