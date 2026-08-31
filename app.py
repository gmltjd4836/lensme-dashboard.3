import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from folium import plugins
from streamlit_folium import st_folium

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
# [탭 1] 상권 지도 분석 (구글 맵 타일 적용)
# ---------------------------------------------------------
with tab_map:
    st.markdown(f'<div class="sub-title">[{candidate_store}] 핵심 상권 지도 (반경 500m)</div>', unsafe_allow_html=True)
    st.markdown("💡 **Tip:** 우측 상단의 `[ ]` 버튼을 누르면 지도를 전체 화면으로 크게 볼 수 있습니다. 마커를 클릭하면 상세 정보가 나옵니다.")
    
    # 천안 불당동 기준 임의 좌표
    center_lat, center_lon = 36.8151, 127.1139 
    
    # 🌟 지도 스타일 변경: 기본 타일을 없애고 구글 맵(Google Maps)을 씌웁니다! (상가 이름, 건물명 표시)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles=None)
    folium.TileLayer(
        tiles='http://mt0.google.com/vt/lyrs=m&hl=ko&x={x}&y={y}&z={z}',
        attr='Google Maps',
        name='Google Maps',
        overlay=False,
        control=True
    ).add_to(m)
    
    # 전체화면 플러그인 추가
    plugins.Fullscreen(position='topright', title='전체화면 확대', title_cancel='전체화면 취소').add_to(m)
    
    # 1. 이전 후보지 마커
    popup_html = f"""
    <div style='width:200px; text-align:center;'>
        <h4 style='color:#e21837; margin-bottom:5px;'>🚩 렌즈미 이전 후보지</h4>
        <b>{candidate_store}</b><br>
        <span style='font-size:12px; color:gray;'>선택된 분석 중심지점</span>
    </div>
    """
    folium.Marker(
        [center_lat, center_lon], 
        tooltip="<b style='font-size:14px; color:#e21837;'>클릭하여 확인 🚩</b>",
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color="red", icon="star", prefix='fa')
    ).add_to(m)
    
    # 2. 반경 500m 핵심 상권 영역
    folium.Circle(
        radius=500, location=[center_lat, center_lon],
        color="#4f46e5", weight=2, fill=True, fill_color="#4f46e5", fill_opacity=0.15,
        tooltip="<b>도보 7~10분 (반경 500m) 핵심 상권 영역</b>"
    ).add_to(m)
    
    # 3. 경쟁사 및 학교 마커 추가
    competitors = []
    if show_olens: competitors.extend([{"name": "오렌즈 불당점", "lat": 36.8165, "lon": 127.1120, "color": "orange", "icon": "eye", "desc": "주요 경쟁사 (컬러렌즈)"}])
    if show_davich: competitors.extend([{"name": "다비치안경 신불당점", "lat": 36.8140, "lon": 127.1155, "color": "blue", "icon": "glasses", "desc": "대형 안경원 (투명/팩렌즈 견제)"}])
    if show_hapa: competitors.extend([{"name": "하파크리스틴 픽업점", "lat": 36.8170, "lon": 127.1145, "color": "pink", "icon": "heart", "desc": "온라인 픽업 중심 거점"}])
    if show_winc: competitors.extend([{"name": "윙크렌즈 안경원", "lat": 36.8135, "lon": 127.1110, "color": "purple", "icon": "dot-circle-o", "desc": "신흥 앱 기반 경쟁사"}])
    
    for comp in competitors:
        comp_html = f"<div style='width:150px;'><b>{comp['name']}</b><br><span style='font-size:12px; color:gray;'>{comp['desc']}</span></div>"
        folium.Marker(
            [comp["lat"], comp["lon"]], 
            tooltip=f"<b style='font-size:13px;'>{comp['name']}</b>",
            popup=folium.Popup(comp_html, max_width=250),
            icon=folium.Icon(color=comp["color"], icon=comp["icon"], prefix='fa')
        ).add_to(m)
        
    if show_school:
        schools = [
            {"name": "불당고등학교", "lat": 36.8185, "lon": 127.1105, "students": "약 950명"},
            {"name": "불당중학교", "lat": 36.8120, "lon": 127.1170, "students": "약 820명"}
        ]
        for sch in schools:
            sch_html = f"<div style='width:150px;'><b>🏫 {sch['name']}</b><br><span style='color:#10b981;'>핵심 타겟: {sch['students']}</span></div>"
            folium.Marker(
                [sch["lat"], sch["lon"]], 
                tooltip=f"<b style='font-size:13px; color:green;'>{sch['name']}</b>",
                popup=folium.Popup(sch_html, max_width=250),
                icon=folium.Icon(color="green", icon="graduation-cap", prefix='fa')
            ).add_to(m)

    # Streamlit에 지도 렌더링
    st_folium(m, width="100%", height=600)
    
    st.info("💡 **상권 종합 브리핑:** 후보지 반경 500m 내에 1020 타겟 학교가 밀집해 있어 잠재 수요가 풍부하나, 오렌즈와 하파크리스틴 등 컬러렌즈 경쟁 강도가 높은 지역입니다. 차별화된 인테리어 및 공격적인 신규 고객 유입 프로모션이 필요합니다.")

# ---------------------------------------------------------
# [탭 2] 상권 매력도 레이더 차트 (As-Is vs To-Be)
# ---------------------------------------------------------
with tab_radar:
    st.markdown(f'<div class="sub-title">{current_store} vs {candidate_store} 입지 지표 비교</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"🏪 **현재 매장:** {current_store}")
        st.markdown(f"🚩 **이전 후보:** {candidate_store}")
        st.markdown("---")
        st.markdown("""
        **[평가 지표 가이드]**
        - **1020 유동인구:** 핵심 타겟층의 통행량
        - **타겟 밀집도:** 학교, 학원가 등 주 고객 체류 비중
        - **경쟁 강도(역산):** 점수가 높을수록 경쟁사가 적어 유리함
        - **임대료 가성비:** 평당 임대료 대비 예상 매출 비율
        - **상권 활력도:** 상권 전체의 성장세 및 공실률
        """)
        
    with col2:
        categories = ['1020 유동인구', '타겟 밀집도', '경쟁 강도(역산)', '임대료 가성비', '상권 활력도']
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
            showlegend=True, margin=dict(t=30, b=30, l=30, r=30),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
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
        monthly_sales = daily_cust * atv * 30
        monthly_gross_profit = monthly_sales * (margin_rate / 100)
        monthly_net_profit = monthly_gross_profit - monthly_rent - monthly_labor
        
        # 보증금 제외 순수 소멸성 비용 기준 회수 기간
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
