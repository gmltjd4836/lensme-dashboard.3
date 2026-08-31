import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from folium import plugins
from streamlit_folium import st_folium
import requests
import urllib.parse

# ==========================================
# 0. 페이지 및 기본 설정
# ==========================================
st.set_page_config(page_title="렌즈미 매장 이전 상권 분석기", page_icon="🗺️", layout="wide")

# 🌟🌟🌟 여기에 발급받으신 [일반 인증키(Encoding)]를 복사해서 큰따옴표("") 안에 넣어주세요! 🌟🌟🌟
API_KEY = "aXN6wwYUtb8cmsw%2FKilpDWQn1wUuT6U1igFdsRMJNBT8%2ByFZY6dQe95h9rrcobd4%2Fz7JQG0e14PuzcIZNd%2BcbQ%3D%3D"

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

st.markdown('<div class="main-title">🗺️ 렌즈미 매장 이전 & 상권 분석 시뮬레이터</div>', unsafe_allow_html=True)

# ==========================================
# 1. 사이드바: 기본 설정
# ==========================================
st.sidebar.title("🔍 상담 기본 정보 설정")
current_store = st.sidebar.text_input("현재 매장명", value="렌즈미 천안쌍용점")
candidate_store = st.sidebar.text_input("이전 후보지 상권명", value="천안 신불당 상권")

st.sidebar.markdown("---")
st.sidebar.info("💡 **API 자동 연동됨**\n코드에 입력된 API 키를 통해 주변 안경원/렌즈샵 데이터를 실시간으로 불러옵니다.")

# ==========================================
# 🚀 소상공인 API 호출 함수 (실제 데이터 가져오기)
# ==========================================
@st.cache_data(ttl=3600) # 한 번 불러온 데이터는 1시간 동안 저장(속도 향상)
def get_real_competitors(lat, lon, key):
    # 키를 안 넣었거나 기본 텍스트면 가짜(샘플) 데이터 반환
    if not key or key == "여기에_사장님의_인증키를_붙여넣으세요":
        return None 
    
    url = "http://apis.data.go.kr/B553077/api/open/sdam/bizesInfoInRadius"
    try:
        params = {
            "ServiceKey": urllib.parse.unquote(key),
            "type": "json",
            "cy": lat,
            "cx": lon,
            "radius": 500,
            "numOfRows": 100
        }
        res = requests.get(url, params=params, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            items = data.get('body', {}).get('items', [])
            real_stores = []
            
            # 받아온 상가 목록 중 '안경'이나 '렌즈'가 포함된 곳만 필터링
            for item in items:
                name = item.get('bizesNm', '')
                if '안경' in name or '렌즈' in name or '다비치' in name or '오렌즈' in name:
                    real_stores.append({
                        'name': name,
                        'lat': float(item.get('lat', 0)),
                        'lon': float(item.get('lon', 0)),
                        'color': 'purple',
                        'icon': 'glasses',
                        'desc': item.get('indsSclsNm', '실제 주변 경쟁사')
                    })
            return real_stores
    except Exception as e:
        return None
    return None

# ==========================================
# 2. 메인 화면 탭 구성
# ==========================================
tab_map, tab_pop, tab_radar, tab_roi = st.tabs([
    "📍 상권 지도 및 경쟁사 분석", 
    "👥 유동인구 및 타겟 분석", 
    "📊 상권 매력도 비교 (As-Is vs To-Be)", 
    "💰 이전 투자금 회수(ROI) 시뮬레이터"
])

# ---------------------------------------------------------
# [탭 1] 상권 지도 분석 (구글 맵 + 진짜 공공데이터 연동)
# ---------------------------------------------------------
with tab_map:
    st.markdown(f'<div class="sub-title">[{candidate_store}] 핵심 상권 지도 (반경 500m)</div>', unsafe_allow_html=True)
    
    # 임의 분석 좌표 (천안 신불당)
    center_lat, center_lon = 36.8151, 127.1139 
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles=None)
    folium.TileLayer(
        tiles='http://mt0.google.com/vt/lyrs=m&hl=ko&x={x}&y={y}&z={z}',
        attr='Google Maps',
        name='Google Maps',
        overlay=False,
        control=True
    ).add_to(m)
    plugins.Fullscreen(position='topright', title='전체화면').add_to(m)
    
    # 이전 후보지 마커
    folium.Marker(
        [center_lat, center_lon], 
        tooltip="<b style='font-size:14px; color:#e21837;'>클릭하여 확인 🚩</b>",
        popup=folium.Popup(f"<b>{candidate_store}</b> (이전 후보지)", max_width=300),
        icon=folium.Icon(color="red", icon="star", prefix='fa')
    ).add_to(m)
    
    # 반경 500m 원
    folium.Circle(
        radius=500, location=[center_lat, center_lon],
        color="#4f46e5", weight=2, fill=True, fill_color="#4f46e5", fill_opacity=0.15,
        tooltip="도보 7~10분 상권 영역"
    ).add_to(m)
    
    # 🌟 API로 진짜 경쟁사 데이터 불러오기 시도
    competitors = get_real_competitors(center_lat, center_lon, API_KEY)
    
    # 만약 키가 없거나 에러가 나면 샘플 데이터 사용
    if competitors is None:
        competitors = [
            {"name": "오렌즈 불당점", "lat": 36.8165, "lon": 127.1120, "color": "orange", "icon": "eye", "desc": "주요 경쟁사"},
            {"name": "다비치안경 신불당점", "lat": 36.8140, "lon": 127.1155, "color": "blue", "icon": "glasses", "desc": "대형 안경원"},
            {"name": "하파크리스틴 픽업점", "lat": 36.8170, "lon": 127.1145, "color": "pink", "icon": "heart", "desc": "온라인 픽업점"}
        ]
        st.warning("⚠️ API 키가 입력되지 않아 임시(샘플) 경쟁사 데이터를 표시합니다.")
    else:
        st.success(f"✅ 공공데이터 서버 연동 성공! 반경 500m 내에 총 {len(competitors)}개의 진짜 안경원/렌즈샵을 찾았습니다.")

    # 지도에 경쟁사 마커 찍기
    for comp in competitors:
        comp_html = f"<div style='width:150px;'><b>{comp['name']}</b><br><span style='font-size:12px; color:gray;'>{comp.get('desc','')}</span></div>"
        folium.Marker(
            [comp["lat"], comp["lon"]], 
            tooltip=f"<b style='font-size:13px;'>{comp['name']}</b>",
            popup=folium.Popup(comp_html, max_width=250),
            icon=folium.Icon(color=comp.get("color", "purple"), icon=comp.get("icon", "glasses"), prefix='fa')
        ).add_to(m)

    st_folium(m, width="100%", height=600)

# ---------------------------------------------------------
# [탭 2] 유동인구 및 타겟 분석 (상담용 시각화 세팅)
# ---------------------------------------------------------
with tab_pop:
    st.markdown(f'<div class="sub-title">👥 [{candidate_store}] 유동인구 분석 보고서</div>', unsafe_allow_html=True)
    st.info("💡 유동인구 데이터는 고가의 유료 통신사 데이터가 필요하므로, 여기서는 점주 상담 설득용으로 가장 이상적인 상권 트래픽 모델을 시각화하여 제공합니다.")

    # KPI 대시보드
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown('<div class="metric-box"><div class="metric-title">일평균 유동인구</div><div class="metric-value">28,450명</div></div>', unsafe_allow_html=True)
    with col2: st.markdown('<div class="metric-box"><div class="metric-title">여성 비율</div><div class="metric-value" style="color:#ec4899;">58.2%</div></div>', unsafe_allow_html=True)
    with col3: st.markdown('<div class="metric-box"><div class="metric-title">1020 타겟 비율</div><div class="metric-value" style="color:#4f46e5;">42.5%</div></div>', unsafe_allow_html=True)
    with col4: st.markdown('<div class="metric-box"><div class="metric-title">최고 혼잡 시간대</div><div class="metric-value">16시 ~ 20시</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        age_data = pd.DataFrame({'연령대': ['10대', '20대', '30대', '40대', '50대 이상'], '유동인구 수': [4200, 7800, 6500, 5100, 4850]})
        fig_age = px.pie(age_data, values='유동인구 수', names='연령대', hole=0.4, title="📊 연령대별 유동인구 비중 (1020 비중 42.5%)", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_age.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_age, use_container_width=True)

    with col_chart2:
        time_data = pd.DataFrame({'시간대': ['06-09시', '09-12시', '12-15시', '15-18시', '18-21시', '21-24시'], '유동인구 수': [1800, 3500, 5200, 8900, 7100, 1950]})
        fig_time = px.line(time_data, x='시간대', y='유동인구 수', markers=True, title="📈 시간대별 유동인구 흐름 (하교/퇴근 시간 집중)", line_shape='spline')
        fig_time.update_traces(line_color='#4f46e5', line_width=3, marker_size=8)
        st.plotly_chart(fig_time, use_container_width=True)

# ---------------------------------------------------------
# [탭 3] 상권 매력도 레이더 차트 
# ---------------------------------------------------------
with tab_radar:
    st.markdown(f'<div class="sub-title">{current_store} vs {candidate_store} 입지 지표 비교</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"🏪 **현재 매장:** {current_store}")
        st.markdown(f"🚩 **이전 후보:** {candidate_store}")
        st.markdown("---")
        st.markdown("- **1020 유동인구:** 핵심 타겟층 통행량\n- **타겟 밀집도:** 학교, 학원가 비중\n- **경쟁 강도(역산):** 점수가 높을수록 경쟁사 적음\n- **임대료 가성비:** 임대료 대비 매출\n- **상권 활력도:** 성장세 및 공실률")
        
    with col2:
        categories = ['1020 유동인구', '타겟 밀집도', '경쟁 강도(역산)', '임대료 가성비', '상권 활력도']
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=[60, 55, 80, 70, 50, 60], theta=categories + [categories[0]], fill='toself', name=current_store, line_color='gray', fillcolor='rgba(128, 128, 128, 0.4)'))
        fig_radar.add_trace(go.Scatterpolar(r=[90, 85, 40, 65, 95, 90], theta=categories + [categories[0]], fill='toself', name=candidate_store, line_color='#ec4899', fillcolor='rgba(236, 72, 153, 0.4)'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, margin=dict(t=30, b=30, l=30, r=30), legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_radar, use_container_width=True)

# ---------------------------------------------------------
# [탭 4] ROI 시뮬레이터 
# ---------------------------------------------------------
with tab_roi:
    st.markdown('<div class="sub-title">💸 예상 매출 및 투자금 회수 시뮬레이터</div>', unsafe_allow_html=True)
    col_input, col_result = st.columns([1, 1.5])
    
    with col_input:
        st.markdown("**1. 예상 투자 비용 설정 (만 원)**")
        deposit = st.number_input("보증금", value=5000, step=1000)
        premium = st.number_input("권리금", value=3000, step=1000)
        interior = st.number_input("인테리어 및 집기 비용", value=6000, step=1000)
        total_investment = deposit + premium + interior
        
        st.markdown("---")
        st.markdown("**2. 예상 매출 및 지출 설정**")
        daily_cust = st.slider("예상 일평균 방문 고객 수 (명)", min_value=10, max_value=150, value=40, step=5)
        atv = st.slider("예상 객단가 (만 원)", min_value=2.0, max_value=8.0, value=3.5, step=0.1)
        margin_rate = st.slider("평균 마진율 (%)", min_value=30, max_value=70, value=45, step=1)
        
        monthly_rent = st.number_input("월 임대료 (만 원)", value=300, step=50)
        monthly_labor = st.number_input("월 인건비 및 기타 고정비 (만 원)", value=400, step=50)
        
    with col_result:
        monthly_sales = daily_cust * atv * 30
        monthly_gross_profit = monthly_sales * (margin_rate / 100)
        monthly_net_profit = monthly_gross_profit - monthly_rent - monthly_labor
        
        sunk_investment = premium + interior
        payback_months = sunk_investment / monthly_net_profit if monthly_net_profit > 0 else 0
            
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-box"><div class="metric-title">총 투자금</div><div class="metric-value">{total_investment:,}만</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-box"><div class="metric-title">예상 월 순수익</div><div class="metric-value" style="color:{"#ef4444" if monthly_net_profit<=0 else "#10b981"}">{int(monthly_net_profit):,}만</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-box"><div class="metric-title">투자금 회수 기간</div><div class="metric-value">{"불가" if payback_months==0 else f"{payback_months:.1f}개월"}</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if monthly_net_profit > 0:
            months = list(range(1, 25))
            accumulated_profit = [(monthly_net_profit * m) - sunk_investment for m in months]
            df_roi = pd.DataFrame({'월(Month)': months, '누적 수익': accumulated_profit})
            fig_bar = px.bar(df_roi, x='월(Month)', y='누적 수익', title=f"⏳ {candidate_store} 이전 시 향후 2년 누적 수익 예측", color='누적 수익', color_continuous_scale=px.colors.diverging.RdYlGn)
            fig_bar.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="손익분기점(BEP)")
            fig_bar.update_layout(xaxis_title="이전 후 개월 수", yaxis_title="누적 수익 (만 원)", showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.error("🚨 예상 월 순수익이 적자입니다.")
