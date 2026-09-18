import streamlit as st
import requests
from datetime import datetime, timedelta, timezone


# --------------------------------------------------
# 1. 페이지 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")


# --------------------------------------------------
# 2. 한국 시간 기준으로 '어제' 계산
# --------------------------------------------------

# 배포 서버가 한국 시간이 아닐 수도 있기 때문에
# UTC+9를 직접 지정해서 한국 시간을 계산합니다.
KST = timezone(timedelta(hours=9))

now_kst = datetime.now(KST)
yesterday = now_kst.date() - timedelta(days=1)

# KOBIS API가 요구하는 날짜 형식: YYYYMMDD
target_dt = yesterday.strftime("%Y%m%d")

st.caption(f"조회 날짜: {yesterday.strftime('%Y년 %m월 %d일')}")


# --------------------------------------------------
# 3. KOBIS API에서 데이터를 가져오는 함수
# --------------------------------------------------

# ttl=3600 → 가져온 결과를 약 1시간 동안 기억합니다.
# 따라서 같은 날짜를 다시 조회해도 API를 계속 호출하지 않습니다.
@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):
    # 인증키는 Streamlit Secrets에서 가져옵니다.
    # 실제 키를 코드에 직접 적지 않습니다.
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
        # KOBIS API에 요청을 보냅니다.
        response = requests.get(url, params=params, timeout=10)

        # HTTP 오류가 발생하면 예외를 발생시킵니다.
        response.raise_for_status()

        # JSON 형태로 응답을 받습니다.
        data = response.json()

    except requests.exceptions.RequestException as e:
        return None, f"API 요청에 실패했습니다: {e}"

    except ValueError:
        return None, "API 응답을 JSON으로 읽을 수 없습니다."

    # --------------------------------------------------
    # 4. 인증키 오류 확인
    # --------------------------------------------------

    # KOBIS는 인증키가 잘못되어도 HTTP 상태코드가 200일 수 있습니다.
    # 따라서 faultInfo가 있는지 직접 확인해야 합니다.
    if "faultInfo" in data:
        fault = data["faultInfo"]

        message = fault.get("message", "알 수 없는 API 오류")
        return None, f"KOBIS API 오류: {message}"

    # --------------------------------------------------
    # 5. 영화 목록 확인
    # --------------------------------------------------

    boxoffice_result = data.get("boxOfficeResult")

    if not boxoffice_result:
        return None, "boxOfficeResult가 응답에 없습니다."

    movie_list = boxoffice_result.get("dailyBoxOfficeList", [])

    if not movie_list:
        return None, "해당 날짜의 영화 목록이 비어 있습니다."

    # 숫자로 사용할 값들을 문자열에서 정수로 변환합니다.
    for movie in movie_list:
        movie["rank"] = int(movie.get("rank", 0))
        movie["rankInten"] = int(movie.get("rankInten", 0))
        movie["audiCnt"] = int(movie.get("audiCnt", 0))
        movie["audiAcc"] = int(movie.get("audiAcc", 0))
        movie["scrnCnt"] = int(movie.get("scrnCnt", 0))
        movie["showCnt"] = int(movie.get("showCnt", 0))

    # 순위 기준으로 다시 정렬합니다.
    movie_list.sort(key=lambda x: x["rank"])

    return movie_list, None


# --------------------------------------------------
# 6. API 호출
# --------------------------------------------------

movies, error_message = get_boxoffice(target_dt)


# --------------------------------------------------
# 7. 오류가 발생했을 때 안내
# --------------------------------------------------

if error_message:
    st.error("박스오피스 정보를 불러오지 못했습니다.")

    st.warning(
        "다음 항목을 확인해 주세요.\n\n"
        "• Streamlit Secrets에 `KOBIS_KEY`가 정확히 등록되어 있는지 확인\n"
        "• KOBIS에서 발급받은 인증키가 유효한지 확인\n"
        "• 인터넷/API 서버에 일시적인 문제가 없는지 확인\n"
        "• 조회 날짜에 박스오피스 데이터가 실제로 제공되는지 확인\n\n"
        f"상세 내용: {error_message}"
    )

    st.stop()


# --------------------------------------------------
# 8. 1위 영화 정보
# --------------------------------------------------

first_movie = movies[0]

st.subheader("🏆 어제의 박스오피스 1위")

st.markdown(f"## {first_movie['movieNm']}")
st.write(f"개봉일: {first_movie['openDt']}")


# 숫자를 보기 좋게 만드는 함수
def number_format(number):
    return f"{number:,}"


# 지표 카드 세 장
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
# 9. 전체 영화 정보를 표로 표시
# --------------------------------------------------

st.subheader("📋 일일 박스오피스")

# 표에 표시할 데이터만 따로 만듭니다.
table_data = []

for movie in movies:
    table_data.append({
        "순위": movie["rank"],
        "영화명": movie["movieNm"],
        "개봉일": movie["openDt"],
        "관객수": movie["audiCnt"],
        "누적관객": movie["audiAcc"],
        "스크린수": movie["scrnCnt"]
    })

st.dataframe(
    table_data,
    use_container_width=True,
    hide_index=True,
    column_config={
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
# 10. 관객수 상위 5편 막대그래프
# --------------------------------------------------

st.subheader("📊 관객수 상위 5편")

# 관객수가 많은 순서대로 정렬합니다.
top5 = sorted(
    movies,
    key=lambda movie: movie["audiCnt"],
    reverse=True
)[:5]

# Streamlit의 기본 막대그래프를 사용하기 위해
# 영화명을 index로 하는 딕셔너리를 만듭니다.
chart_data = {
    movie["movieNm"]: movie["audiCnt"]
    for movie in top5
}

st.bar_chart(chart_data)


# --------------------------------------------------
# 11. 데이터 출처
# --------------------------------------------------

st.caption(
    "데이터 출처: 영화관입장권통합전산망(KOBIS) 일일 박스오피스 API"
)
