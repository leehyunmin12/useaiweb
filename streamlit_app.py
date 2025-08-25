# streamlit_app.py

import streamlit as st
import pandas as pd
import requests # API 요청을 보내기 위한 라이브러리

# --- 1. API 데이터 호출 함수 ---
@st.cache_data(ttl=3600) # 1시간(3600초) 동안 데이터 캐싱
def fetch_data_from_api(city_name):
    """경기도 공공데이터 API를 호출하여 특정 시군의 지역화폐 가맹점 데이터를 가져오는 함수"""
    
    # 중요: 아래 YOUR_PERSONAL_API_KEY 부분에 선생님께서 발급받은 개인 인증키를 붙여넣으세요!
    API_KEY = "309444ab01524ccfba96afb7bddc8a38" 
    URL = f"https://openapi.gg.go.kr/RegionMnyFacltStus?KEY={API_KEY}&Type=json&pIndex=1&pSize=1000&SIGUN_NM={city_name}"

    # API 키가 입력되지 않은 경우 사용자에게 안내
    if API_KEY == "YOUR_PERSONAL_API_KEY" or not API_KEY:
        st.error("오류: 개인 API 키가 입력되지 않았습니다. 위의 코드에서 API_KEY 값을 수정해주세요.")
        return pd.DataFrame()

    try:
        response = requests.get(URL)
        if response.status_code != 200:
            st.error(f"API 서버 응답 오류: Status Code {response.status_code}")
            return pd.DataFrame()
        
        data = response.json()
        
        # API 응답에 데이터가 있는지 확인
        if 'RegionMnyFacltStus' not in data or not data['RegionMnyFacltStus'][1]['row']:
            st.warning(f"'{city_name}'에 대한 가맹점 데이터가 없습니다.")
            return pd.DataFrame()
            
        items = data['RegionMnyFacltStus'][1]['row']
        df = pd.DataFrame(items)
        
        df['REFINE_WGS84_LAT'] = pd.to_numeric(df['REFINE_WGS84_LAT'], errors='coerce')
        df['REFINE_WGS84_LOGT'] = pd.to_numeric(df['REFINE_WGS84_LOGT'], errors='coerce')
        df.dropna(subset=['REFINE_WGS84_LAT', 'REFINE_WGS84_LOGT'], inplace=True)
        
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"네트워크 오류: API 서버에 접속할 수 없습니다. 인터넷 연결을 확인해주세요. ({e})")
        return pd.DataFrame()
    except (KeyError, IndexError):
        st.error("API 응답 데이터 형식이 예상과 다릅니다. API 명세가 변경되었을 수 있습니다.")
        # 디버깅을 위해 실제 응답 내용 출력
        st.json(data)
        return pd.DataFrame()


# --- 2. 앱 UI 구성 (이전과 동일) ---

st.title('📍 지역별 지역화폐 사용 가능점 표시 (API 연동)')

gyeonggi_cities = [
    '가평군', '고양시', '과천시', '광명시', '광주시', '구리시', '군포시',
    '김포시', '남양주시', '동두천시', '부천시', '성남시', '수원시', '시흥시',
    '안산시', '안성시', '안양시', '양주시', '양평군', '여주시', '연천군',
    '오산시', '용인시', '의왕시', '의정부시', '이천시', '파주시', '평택시',
    '포천시', '하남시', '화성시'
]

with st.sidebar:
    st.header('검색 필터')
    selected_city = st.selectbox('지역을 선택하세요.', options=gyeonggi_cities)

df = fetch_data_from_api(selected_city)

if not df.empty:
    with st.sidebar:
        unique_categories = sorted(df['INDUTYPE_NM'].dropna().unique())
        selected_category = st.selectbox(
            '업종을 선택하세요.',
            options=['전체'] + unique_categories
        )

    if selected_category != '전체':
        filtered_df = df[df['INDUTYPE_NM'] == selected_category]
    else:
        filtered_df = df.copy()

    # --- 4. 결과 표시 (이전과 동일) ---
    st.header(f"'{selected_city}' 지역 '{selected_category}' 가맹점 정보")
    st.write(f"총 **{len(filtered_df)}**개의 가맹점을 찾았습니다.")

    if not filtered_df.empty:
        map_df = filtered_df.rename(columns={'REFINE_WGS84_LAT': 'lat', 'REFINE_WGS84_LOGT': 'lon'})
        st.subheader('🗺️ 가맹점 지도')
        st.map(map_df[['lat', 'lon']])
        
        st.subheader('📋 가맹점 목록')
        display_columns = ['CMPNM_NM', 'INDUTYPE_NM', 'REFINE_ROADNM_ADDR']
        st.dataframe(filtered_df[display_columns].rename(columns={
            'CMPNM_NM': '상호명',
            'INDUTYPE_NM': '업종',
            'REFINE_ROADNM_ADDR': '도로명주소'
        }), use_container_width=True)
    else:
        st.warning("선택하신 업종에 해당하는 가맹점이 없습니다.")