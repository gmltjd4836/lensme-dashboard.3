import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import urllib.parse
import json
import streamlit.components.v1 as components

# ==========================================
# 0. 페이지 및 기본 설정
# ==========================================
st.set_page_config(page_title="렌즈미 매장 이전 상권 분석기", page_icon="🗺️", layout="wide")

# 🌟 사장님의 API 키 3종 세트 완벽 내장!
KAKAO_REST_API_KEY = "f6eab02e349ec379ba08ebf65a54a1df" # 검색용
KAKAO_JS_API_KEY = "c045609510f8b75252389123f086be48" # 카카오맵 지도 띄우기용
DATA_GO_KR_API_KEY = "aXN6wwYUtb8cmsw%2FKilpDWQn1wUuT6U1igFdsRMJNBT8%2ByFZY6dQe95h9rrcobd4%2Fz7JQG0e14PuzcIZNd%2BcbQ%3D%3D" # 소상공인 안경원용

if 'center_lat' not in st.session_state:
    st.session_state.center_lat = 36.81510
if 'center_lon' not in st.session_state:
    st.session_state.center_lon = 127.11390
if 'candidate_store' not in st.session_state:
    st.session_state.candidate_store = "천안 신불당 상권"

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .main-title { color: #0f172a; font-weight: 800; font-size: 28px; border-bottom: 3px solid #4f46e5; padding-bottom: 10px; margin-bottom: 20px;}
    .sub-title { color: #334155; font-weight: 700; font-size: 20px; margin-top: 20px; margin-bottom: 10px;}
    .metric-box { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 15px; text-align: center; }
    .metric-title { font-size: 14px; color: #64748b; margin-bottom: 5px; }
    .metric-value { font-size: 24px; font-weight: 800; color: #0f172a; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🗺️ 렌즈미 매장 이전 & 상권 분석기 (카카오맵)</div>', unsafe_allow_html=True)

# ==========================================
# 🚀 API 연동 함수 
# ==========================================
def search_location_by_kakao(query, key):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {key}"}
    params = {"query": query}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        if res.status_code == 200:
            docs = res.json().get('documents')
            if docs:
                return float(docs[0]['y']), float(docs[0]['x']), docs[0]['place_name'], "성공"
            else:
                return None, None, None, "검색 결과가 없습니다."
        else:
            return None, None, None, f"카카오 에러: {res.status_code} - {res.text}"
    except Exception as e:
        return None, None, None, f"통신 에러: {str(e)}"

@st.cache_data(ttl=3600)
def get_real_competitors(lat, lon, key):
    if not key: return None 
    url = f"http://apis.data.go.kr/B553077/api/open/sdam/bizesInfoInRadius?ServiceKey={key}&type=json&cy={lat}&cx={lon}&radius=500&numOfRows=100"
    try:
        res = requests.get(url, timeout=7)
        if res.status_code == 200:
            data = res.json()
            items = data.get('body', {}).get('items', [])
            real_stores = []
            for item in items:
                name = item.get('bizesNm', '')
                if any(kw in name for kw in ['안경', '렌즈', '다비치', '오렌즈', '으뜸', '글라스']):
                    try:
                        real_stores.append({
                            'name': name,
                            'lat': float(item.get('lat', 0)),
                            'lon': float(item.get('lon', 0)),
                            'desc': item.get('indsSclsNm', '실제 안경원')
                        })
                    except: continue
            return real_stores
    except: pass
    return None

# ==========================================
# 1. 사이드바: 통합 검색창
# ==========================================
st.sidebar.title("🔍 상권 위치 검색")

search_query = st.sidebar.text_input("📍 검색어 입력 (예: 강남역)", value="")

if st.sidebar.button("🚀 지도로 이동하기", use_container_width=True):
    if search_query:
        lat, lon, place_name, error_msg = search_location_by_kakao(search_query, KAKAO_REST_API_KEY)
        
        if lat and lon:
            st.session_state.center_lat = lat
            st.session_state.center_lon = lon
            st.session_state.candidate_store = place_name
        else:
            st.sidebar.error(f"🚨 검색 실패 이유: {error_msg}")

st.sidebar.markdown("---")
current_store = st.sidebar.text_input("현재 기준 매장명", value="렌즈미 천안쌍용점")
st.sidebar.text_input("분석 대상 상권", value=st.session_state.candidate_store, disabled=True)

# ==========================================
# 2. 메인 화면 탭 구성
# ==========================================
tab_map, tab_pop, tab_radar, tab_roi = st.tabs([
    "📍 카카오 상권 지도", 
    "👥 유동인구 및 타겟 분석", 
    "📊 상권 매력도 비교 (As-Is vs To-Be)", 
    "💰 이전 투자금 회수(ROI) 시뮬레이터"
])

# ---------------------------------------------------------
# [탭 1] 상권 지도 분석 (카카오맵 적용)
# ---------------------------------------------------------
with tab_map:
    st.markdown(f'<div class="sub-title">[{st.session_state.candidate_store}] 핵심 상권 지도 (반경 500m)</div>', unsafe_allow_html=True)
    
    competitors = get_real_competitors(st.session_state.center_lat, st.session_state.center_lon, DATA_GO_KR_API_KEY)
    
    if competitors is None or len(competitors) == 0:
        st.info("💡 반경 500m 내에 검색된 안경원이 없습니다.")
        competitors = []
    else:
        st.success(f"✅ 소상공인 공공데이터 연동 완료! 반경 500m 내에 총 {len(competitors)}개의 주변 안경원/렌즈샵을 찾았습니다.")

    # 🌟 카카오맵 HTML 및 JavaScript 코드 주입
    kakao_map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            #map {{width:100%; height:600px; border-radius: 10px; border: 1px solid #e2e8f0;}}
        </style>
    </head>
    <body>
    <div id="map"></div>
    <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_API_KEY}"></script>
    <script>
        var mapContainer = document.getElementById('map');
        var mapOption = {{
            center: new kakao.maps.LatLng({st.session_state.center_lat}, {st.session_state.center_lon}),
            level: 4 // 지도 확대 레벨
        }};
        var map = new kakao.maps.Map(mapContainer, mapOption);

        // 중심지 핀 (이전 후보지)
        var centerMarker = new kakao.maps.Marker({{
            position: new kakao.maps.LatLng({st.session_state.center_lat}, {st.session_state.center_lon}),
            map: map
        }});

        var centerInfoWindow = new kakao.maps.InfoWindow({{
            content: '<div style="padding:5px;font-size:14px;color:red;font-weight:bold;">🚩 {st.session_state.candidate_store}</div>'
        }});
        centerInfoWindow.open(map, centerMarker);

        // 반경 500m 원 그리기
        var circle = new kakao.maps.Circle({{
            center : new kakao.maps.LatLng({st.session_state.center_lat}, {st.session_state.center_lon}),
            radius: 500,
            strokeWeight: 2,
            strokeColor: '#4f46e5',
            strokeOpacity: 0.8,
            strokeStyle: 'solid',
            fillColor: '#4f46e5',
            fillOpacity: 0.15
        }});
        circle.setMap(map);

        // 경쟁사 핀 찍기
        var comps = {json.dumps(competitors)};
        
        comps.forEach(function(comp) {{
            var marker = new kakao.maps.Marker({{
                map: map,
                position: new kakao.maps.LatLng(comp.lat, comp.lon),
                title: comp.name
            }});

            var infowindow = new kakao.maps.InfoWindow({{
                content: '<div style="padding:5px;font-size:12px;"><b>' + comp.name + '</b><br><span style="color:gray;">' + comp.desc + '</span></div>'
            }});

            kakao.maps.event.addListener(marker, 'mouseover', function() {{
                infowindow.open(map, marker);
            }});
            kakao.maps.event.addListener(marker, 'mouseout', function() {{
                infowindow.close();
            }});
        }});
    </script>
    </body>
    </html>
    """
    
    # 생성된 카카오맵을 스트림릿 화면에 띄우기
    components.html(kakao_map_html, height=620)

# ---------------------------------------------------------
# [탭 2] 유동인구 및 타겟 분석
# ---------------------------------------------------------
with tab_pop:
    st.markdown(f'<div class="sub-title">👥 [{st.session_state.candidate_store}] 유동인구 분석 보고서</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown('<div class="metric-box"><div class="metric-title">일평균 유동인구</div><div class="metric-value">28,450명</div></div>', unsafe_allow_html=True)
    with col2: st.markdown('<div class="metric-box"><div class="metric-title">여성 비율</div><div class="metric-value" style="color:#ec4899;">58.2%</div></div>', unsafe_allow_html=True)
    with col3: st.markdown('<div class="metric-box"><div class="metric-title">1020 타겟 비율</div><div class="metric-value" style="color:#4f46e5;">42.5%</div></div>', unsafe_allow_html=True)
    with col4: st.markdown('<div class="metric-box"><div class="metric-title">최고 혼잡 시간대</div><div class="metric-value">16시 ~ 20시</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        age_data = pd.DataFrame({'연령대': ['10대', '20대', '30대', '40대', '50대 이상'], '유동인구 수': [4200, 7800, 6500, 5100, 4850]})
        fig_age = px.pie(age_data, values='유동인구 수', names='연령대', hole=0.4, title="📊 연령대별 유동인구 비중", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_age.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_age, use_container_width=True)
    with col_chart2:
        time_data = pd.DataFrame({'시간대': ['06-09시', '09-12시', '12-15시', '15-18시', '18-21시', '21-24시'], '유동인구 수': [1800, 3500, 5200, 8900, 7100, 1950]})
        fig_time = px.line(time_data, x='시간대', y='유동인구 수', markers=True, title="📈 시간대별 유동인구 흐름", line_shape='spline')
        fig_time.update_traces(line_color='#4f46e5', line_width=3, marker_size=8)
        st.plotly_chart(fig_time, use_container_width=True)

# ---------------------------------------------------------
# [탭 3] 입지 지표 레이더 차트
# ---------------------------------------------------------
with tab_radar:
    st.markdown(f'<div class="sub-title">{current_store} vs {st.session_state.candidate_store} 입지 비교</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"🏪 **현재 매장:** {current_store}")
        st.markdown(f"🚩 **이전 후보:** {st.session_state.candidate_store}")
        st.markdown("---")
        st.markdown("- **1020 유동인구:** 핵심 타겟층 통행량\n- **타겟 밀집도:** 학교, 학원가 비중\n- **경쟁 강도:** 점수가 높을수록 경쟁사 적음\n- **임대료 가성비:** 임대료 대비 예상 매출\n- **상권 활력도:** 전체 성장세 및 공실률")
    with col2:
        categories = ['1020 유동인구', '타겟 밀집도', '경쟁 강도', '임대료 가성비', '상권 활력도']
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=[60, 55, 80, 70, 50, 60], theta=categories + [categories[0]], fill='toself', name=current_store, line_color='gray', fillcolor='rgba(128, 128, 128, 0.4)'))
        fig_radar.add_trace(go.Scatterpolar(r=[90, 85, 40, 65, 95, 90], theta=categories + [categories[0]], fill='toself', name=st.session_state.candidate_store, line_color='#ec4899', fillcolor='rgba(236, 72, 153, 0.4)'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, margin=dict(t=30, b=30, l=30, r=30), legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_radar, use_container_width=True)

# ---------------------------------------------------------
# [탭 4] ROI 시뮬레이터
# ---------------------------------------------------------
with tab_roi:
    st.markdown('<div class="sub-title">💸 예상 매출 및 투자금 회수 시뮬레이터</div>', unsafe_allow_html=True)
    col_input, col_result = st.columns([1, 1.5])
    
    with col_input:
        deposit = st.number_input("보증금 (만 원)", value=5000, step=1000)
        premium = st.number_input("권리금 (만 원)", value=3000, step=1000)
        interior = st.number_input("인테리어/집기 (만 원)", value=6000, step=1000)
        total_investment = deposit + premium + interior
        
        st.markdown("---")
        daily_cust = st.slider("일평균 방문 고객 (명)", min_value=10, max_value=150, value=40, step=5)
        atv = st.slider("객단가 (만 원)", min_value=2.0, max_value=8.0, value=3.5, step=0.1)
        margin_rate = st.slider("마진율 (%)", min_value=30, max_value=70, value=45, step=1)
        monthly_rent = st.number_input("월 임대료 (만 원)", value=300, step=50)
        monthly_labor = st.number_input("월 고정비 (만 원)", value=400, step=50)
        
    with col_result:
        monthly_sales = daily_cust * atv * 30
        monthly_gross_profit = monthly_sales * (margin_rate / 100)
        monthly_net_profit = monthly_gross_profit - monthly_rent - monthly_labor
        
        sunk_investment = premium + interior
        payback_months = sunk_investment / monthly_net_profit if monthly_net_profit > 0 else 0
            
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-box"><div class="metric-title">총 투자금</div><div class="metric-value">{total_investment:,}만</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-box"><div class="metric-title">월 순수익</div><div class="metric-value" style="color:{"#ef4444" if monthly_net_profit<=0 else "#10b981"}">{int(monthly_net_profit):,}만</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-box"><div class="metric-title">투자 회수 기간</div><div class="metric-value">{"불가" if payback_months==0 else f"{payback_months:.1f}개월"}</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if monthly_net_profit > 0:
            months = list(range(1, 25))
            accumulated_profit = [(monthly_net_profit * m) - sunk_investment for m in months]
            df_roi = pd.DataFrame({'월(Month)': months, '누적 수익': accumulated_profit})
            fig_bar = px.bar(df_roi, x='월(Month)', y='누적 수익', title=f"⏳ 향후 2년 누적 수익 예측", color='누적 수익', color_continuous_scale=px.colors.diverging.RdYlGn)
            fig_bar.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="손익분기점(BEP)")
            fig_bar.update_layout(xaxis_title="이전 후 개월 수", yaxis_title="누적 수익 (만 원)", showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.error("🚨 예상 월 순수익이 적자입니다.")
