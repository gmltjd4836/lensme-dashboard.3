import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium
import math

# ==========================================
# 0. 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="렌즈미 매장 이전 상권 분석기", page_icon="🗺️", layout="wide")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .main-title { color: #0f172a; font-weight: 800; font-size: 28px; border-bottom: 3px solid #4f46e5; padding-bottom: 10px; margin-bottom: 20px;}
    .sub-title { color: #334155; font-weight: 700; font-size: 20px; margin-top: 20px; margin-bottom: 10px;}
    .highlight { color: #4f46e5; font-weight: 800; }
    .metric-box { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 15px; text-align: center; }
    .metric-title { font-size: 14px; color: #64748b; margin-bottom: 5px; }
    .metric-value { font-size: 24px; font-weight: 800; color: #0f172a; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🗺️ 렌즈미 매장 이전 & 상권 분석 시뮬레이터</div>', unsafe_allow_html=True)

# ==========================================
# 1. 사이드바: 상권 기본 정보 입력
# ==========================================
st.sidebar.title("🔍 상담 기본 정보 설정")
st.sidebar.markdown("현재 매장과 이전 후보지를 설정하세요.")

current_store = st.sidebar.text_input("현재 매장명", value="렌즈미 천안쌍용점")
candidate_store = st.sidebar.text_input("이전 후보지 상권명", value="천안 신불당 상권")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 경쟁사 및 타겟 필터 (지도 표시용)")
show_olens = st.sidebar.checkbox("🟠 오렌즈 (Olens)", value=True)
show_davich = st.sidebar.checkbox("🔵 다비치안경 (Davich)", value=True)
show_hapa = st.sidebar.checkbox("🌸 하파크리스틴 (Hapa Kristin)", value=True)
show_winc = st.sidebar.checkbox("🟣 윙크렌즈 (Winc Lens)", value=True)
show_school = st.sidebar.checkbox("🏫 중·고등학교 / 대학교", value=True)

# ==========================================
# 2. 메인 화면 탭 구성
# ==========================================
tab_map, tab_radar, tab_roi = st.tabs(["📍 상권 지도 및 경쟁사 분석", "📊 상권 매력도 비교 (As-Is vs To-Be)", "💰 이전 투자금 회수(ROI) 시뮬레이터"])

# ---------------------------------------------------------
# [탭 1] 상권 지도 분석 (Folium)
# ---------------------------------------------------------
with tab_map:
    st.markdown(f'<div class="sub-title">[{candidate_store}] 반경 500m 상권 현황</div>', unsafe_allow_html=True)
    st.markdown("후보지 주변의 주요 경쟁사와 1020 타겟 집객 시설(학교 등)을 확인합니다.")
    
    # 💡 실제 서비스 시에는 카카오/네이버 지도 API로 위경도를 불러와야 합니다.
    # 여기서는 시각적 연출을 위해 임의의 좌표(천안 불당동 부근)를 사용한 목업(Mock) 데이터입니다.
    center_lat, center_lon = 36.8151, 127.1139 
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles="CartoDB positron")
    
    # 1. 이전 후보지 마커
    folium.Marker(
        [center_lat, center_lon], tooltip="이전 후보지 (렌즈미)",
        icon=folium.Icon(color="red", icon="star", prefix='fa')
    ).add_to(m)
    
    # 2. 반경 500m 원 그리기
    folium.Circle(
        radius=500, location=[center_lat, center_lon],
        color="#4f46e5", fill=True, fill_color="#4f46e5", fill_opacity=0.1
    ).add_to(m)
    
    # 3. 경쟁사 및 학교 마커 추가 (가상 좌표)
    competitors = []
    if show_olens: competitors.extend([{"name": "오렌즈 불당점", "lat": 36.8165, "lon": 127.1120, "color": "orange", "icon": "eye"}])
    if show_davich: competitors.extend([{"name": "다비치안경 신불당점", "lat": 36.8140, "lon": 127.1155, "color": "blue", "icon": "glasses"}])
    if show_hapa: competitors.extend([{"name": "하파크리스틴 픽업점", "lat": 36.8170, "lon": 127.1145, "color": "pink", "icon": "heart"}])
    if show_winc: competitors.extend([{"name": "윙크렌즈 안경원", "lat": 36.8135, "lon": 127.1110, "color": "purple", "icon": "dot-circle-o"}])
    
    for comp in competitors:
        folium.Marker(
            [comp["lat"], comp["lon"]], tooltip=comp["name"],
            icon=folium.Icon(color=comp["color"], icon=comp["icon"], prefix='fa')
        ).add_to(m)
        
    if show_school:
        schools = [
            {"name": "불당고등학교", "lat": 36.8185, "lon": 127.1105},
            {"name": "불당중학교", "lat": 36.8120, "lon": 127.1170}
        ]
        for sch in schools:
            folium.Marker(
                [sch["lat"], sch["lon"]], tooltip=sch["name"],
                icon=folium.Icon(color="green", icon="graduation-cap", prefix='fa')
            ).add_to(m)

    # Streamlit에 지도 렌더링
    st_folium(m, width=1200, height=500)
    
    st.info("💡 **상권 요약:** 후보지 반경 500m 내에 1020 타겟 학교가 밀집해 있으나, 오렌즈와 하파크리스틴 등 컬러렌즈 경쟁 강도가 높은 지역입니다. (차별화된 인테리어 및 팩렌즈 공격적 마케팅 필요)")

# ---------------------------------------------------------
# [탭 2] 상권 매력도 레이더 차트 (As-Is vs To-Be)
# ---------------------------------------------------------
with tab_radar:
    st.markdown(f'<div class="sub-title">{current_store} vs {candidate_store} 입지 지표 비교</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"**현재:** {current_store}")
        st.markdown(f"**후보:** {candidate_store}")
        st.markdown("---")
        st.markdown("- **1020 유동인구:** 해당 상권을 지나가는 주요 타겟층의 규모\n- **타겟 밀집도:** 학교, 학원가 등 주 고객층 체류 시설 비중\n- **경쟁 강도:** 주변 경쟁사(오렌즈, 다비치 등) 밀집도 (낮을수록 점수 높음)\n- **임대료 가성비:** 평당 임대료 대비 예상 매출액 비율\n- **상권 활력도:** 공실률, 신규 브랜드 입점 등 상권의 성장성")
        
    with col2:
        categories = ['1020 유동인구', '타겟 밀집도', '경쟁 강도(역산)', '임대료 가성비', '상권 활력도']
        # 임의의 스코어 세팅 (1~100점)
        current_scores = [60, 55, 80, 70, 50] 
        candidate_scores = [90, 85, 40, 65, 95] 
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=current_scores + [current_scores[0]], theta=categories + [categories[0]],
            fill='toself', name=current_store, line_color='gray', fillcolor='rgba(128, 128, 128, 0.4)'
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=candidate_scores + [candidate_scores[0]], theta=categories + [categories[0]],
            fill='toself', name=candidate_store, line_color='#ec4899', fillcolor='rgba(236, 72, 153, 0.4)'
        ))
        
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True, margin=dict(t=30, b=30, l=30, r=30)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# ---------------------------------------------------------
# [탭 3] ROI 시뮬레이터 (투자금 회수 기간 계산)
# ---------------------------------------------------------
with tab_roi:
    st.markdown('<div class="sub-title">💸 예상 매출 및 투자금 회수 시뮬레이터</div>', unsafe_allow_html=True)
    
    col_input, col_result = st.columns([1, 1.5])
    
    with col_input:
        st.markdown("**1. 예상 투자 비용 설정 (단위: 만 원)**")
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
        # 월 매출 및 순수익 계산
        monthly_sales = daily_cust * atv * 30
        monthly_gross_profit = monthly_sales * (margin_rate / 100)
        monthly_net_profit = monthly_gross_profit - monthly_rent - monthly_labor
        
        # 회수 기간 계산 (보증금 제외 순수 소멸성 비용 기준 회수 기간)
        sunk_investment = premium + interior
        if monthly_net_profit > 0:
            payback_months = sunk_investment / monthly_net_profit
        else:
            payback_months = 0
            
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-box"><div class="metric-title">총 투자금</div><div class="metric-value">{total_investment:,}만</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-box"><div class="metric-title">예상 월 순수익</div><div class="metric-value" style="color:{"#ef4444" if monthly_net_profit<=0 else "#10b981"}">{int(monthly_net_profit):,}만</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-box"><div class="metric-title">투자금 회수 기간</div><div class="metric-value">{"불가" if payback_months==0 else f"{payback_months:.1f}개월"}</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if monthly_net_profit > 0:
            # 향후 24개월간의 누적 수익 그래프
            months = list(range(1, 25))
            accumulated_profit = [(monthly_net_profit * m) - sunk_investment for m in months]
            
            df_roi = pd.DataFrame({'월(Month)': months, '누적 순수익 (권리/인테리어 차감 후)': accumulated_profit})
            
            fig_bar = px.bar(df_roi, x='월(Month)', y='누적 순수익 (권리/인테리어 차감 후)', 
                             title=f"⏳ {candidate_store} 이전 시 향후 2년 누적 수익 예측",
                             color='누적 순수익 (권리/인테리어 차감 후)', 
                             color_continuous_scale=px.colors.diverging.RdYlGn)
                             
            fig_bar.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="손익분기점(BEP)")
            fig_bar.update_layout(xaxis_title="이전 후 개월 수", yaxis_title="누적 순수익 (만 원)", showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.error("🚨 예상 월 순수익이 적자입니다. 고객 수, 객단가를 높이거나 월세/인건비 등 고정비를 줄여야 합니다.")
