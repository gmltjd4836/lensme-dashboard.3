import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from folium import plugins
from streamlit_folium import st_folium
import requests
import urllib.parse
import os
import glob

# ==========================================
# 0. 페이지 기본 설정 및 API 키
# ==========================================
st.set_page_config(page_title="렌즈미 가맹점 컨설팅 시스템", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")

# 🌟 소상공인(경쟁사 핀) API 키는 발급받으시면 아래 큰따옴표 안에 넣어주세요!
DATA_GO_KR_API_KEY = "여기에_소상공인_인증키를_붙여넣으세요"

# 🌟 사장님이 찾아주신 카카오 API 키를 코드에 완벽하게 내장했습니다!
KAKAO_REST_API_KEY = "f6eab02e349ec379ba08ebf65a54a1df"

# ==========================================
# 🔐 1. 담당자 계정 관리 (아이디, 비밀번호, 표시할 이름)
# ==========================================
USER_DB = {
    "박희성": {"pw": "1234", "name": "박희성 사원"},
    "최산": {"pw": "5678", "name": "최산 사원"},
    "김동훈": {"pw": "123456", "name": "김동훈 과장"}
}

# 세션 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = ""
    st.session_state.display_name = ""

if 'center_lat' not in st.session_state: st.session_state.center_lat = 36.81510
if 'center_lon' not in st.session_state: st.session_state.center_lon = 127.11390
if 'candidate_store' not in st.session_state: st.session_state.candidate_store = "천안 신불당 상권"

# 로그인 화면
if not st.session_state.logged_in:
    st.markdown("""
    <div style='text-align: center; margin-top: 100px;'>
        <h1 style='color: #0f172a;'>🔐 렌즈미 가맹점 컨설팅 시스템</h1>
        <p style='color: #64748b;'>부여받은 사원 아이디와 비밀번호로 로그인해 주세요.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            user_id = st.text_input("아이디")
            user_pw = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인", use_container_width=True)
            
            if submitted:
                if user_id in USER_DB and USER_DB[user_id]["pw"] == user_pw:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.display_name = USER_DB[user_id]["name"]
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
    st.stop()

# ==========================================
# 📁 2. 사용자별 데이터 저장 폴더
# ==========================================
BASE_SAVE_DIR = "uploaded_data"
USER_SAVE_DIR = os.path.join(BASE_SAVE_DIR, st.session_state.user_id)
if not os.path.exists(USER_SAVE_DIR):
    os.makedirs(USER_SAVE_DIR)

# ==========================================
# 🎨 3. 커스텀 CSS & 공통 함수
# ==========================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    .stApp { background-color: #f8fafc; }
    section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    .header-banner { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 24px 32px; border-radius: 16px; color: white; margin-bottom: 24px; }
    .header-title { font-size: 26px; font-weight: 700; margin: 0; }
    .header-subtitle { font-size: 14px; color: #94a3b8; margin-top: 6px; }
    .metric-card, .metric-box { background-color: #ffffff; padding: 15px 12px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.02); margin-bottom: 12px; text-align:center;}
    .metric-label, .metric-title { font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 4px; }
    .metric-value { font-size: 20px; font-weight: 800; color: #0f172a; }
    .border-indigo { border-top: 4px solid #4f46e5; }
    .border-emerald { border-top: 4px solid #10b981; }
    .border-amber { border-top: 4px solid #f59e0b; }
    .border-violet { border-top: 4px solid #8b5cf6; }
    .border-pink { border-top: 4px solid #ec4899; }
</style>
""", unsafe_allow_html=True)

CATEGORY_COLORS = {
    'OEM': '#4f46e5', 'PB': '#10b981', '글로벌': '#f59e0b', '기타': '#64748b',
    '투명': '#3b82f6', '컬러': '#ec4899', '해당없음(부대용품)': '#94a3b8'
}

# (매출분석용 엑셀 로드 함수)
def get_safe_column(df, possible_names, fallback_idx=None):
    for name in possible_names:
        if name in df.columns: return df[name]
    if fallback_idx is not None and fallback_idx < len(df.columns): return df.iloc[:, fallback_idx]
    return pd.Series([''] * len(df))

@st.cache_data
def load_data(file_paths):
    all_dfs = []
    for file_path in file_paths:
        try:
            df = pd.read_excel(file_path)
            df['파일명'] = os.path.basename(file_path)
            df.columns = df.columns.astype(str).str.replace(' ', '').str.replace('\n', '').str.strip()
            
            df['전표번호_임시'] = get_safe_column(df, ['전표번호', '영수증번호', '주문번호'])
            df['일자_임시'] = get_safe_column(df, ['방문일자', '일자', '날짜', '결제일', '판매일'], 0)
            df['상품명_임시'] = get_safe_column(df, ['상품명2', '상품명', '제품명'])
            df['금액_임시'] = get_safe_column(df, ['금액', '판매금액', '결제금액', '매출액'])
            df['수량_임시'] = get_safe_column(df, ['합계', '수량', '판매수량'])
            df['공급단가_임시'] = get_safe_column(df, ['공급단가', '원가', '단가'], 11)
            df['고객명_임시'] = get_safe_column(df, ['고객명', '회원명', '이름', '수령고객명'], 28)
            df['전화번호_임시'] = get_safe_column(df, ['전화번호', '핸드폰', '연락처', '휴대폰'], 31)
            df['품목그룹1_임시'] = get_safe_column(df, ['품목그룹1', '그룹1'])
            df['품목그룹3_임시'] = get_safe_column(df, ['품목그룹3', '그룹3'])
            df['품목그룹4_임시'] = get_safe_column(df, ['품목그룹4', '그룹4'])
            df['생산업체_임시'] = get_safe_column(df, ['생산업체', '제조사', '브랜드'])
            df['거래처_임시'] = get_safe_column(df, ['거래처(부서)', '거래처', '매장명', '지점명'])

            df = df[df['전표번호_임시'] != '']
            df = df.dropna(subset=['전표번호_임시'])
            df = df[~df['일자_임시'].astype(str).str.contains('합', na=False)]
            
            for kw in ['글라스미', '안경테', '안경렌즈']:
                df = df[~df['상품명_임시'].fillna('').astype(str).str.contains(kw)]
            
            def to_num(s): return pd.to_numeric(s.astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            df['금액'] = to_num(df['금액_임시'])
            df['합계'] = to_num(df['수량_임시'])
            df['공급단가'] = to_num(df['공급단가_임시'])
            df['총원가'] = df['공급단가'] * df['합계']
            df['총마진'] = df['금액'] - df['총원가']
            
            df['상품명2'] = df['상품명_임시'].fillna('-')
            df['생산업체'] = df['생산업체_임시'].fillna('미지정')
            df['품목그룹1'] = df['품목그룹1_임시'].fillna('미지정')
            df['품목그룹3'] = df['품목그룹3_임시'].fillna('미지정')
            df['품목그룹4'] = df['품목그룹4_임시'].fillna('미지정')
            df['거래처(부서)'] = df['거래처_임시'].fillna('미지정')
            df['전표번호'] = df['전표번호_임시']
            df['방문일자'] = df['일자_임시'].astype(str).str[:10]
            df['날짜_변환'] = pd.to_datetime(df['방문일자'], errors='coerce')
            df['연도'] = df['날짜_변환'].dt.year.fillna(0).astype(int).astype(str).replace('0', '연도미상')
            df['월'] = df['날짜_변환'].dt.month
            df['고객명_정제'] = df['고객명_임시'].fillna('').astype(str).str.strip().replace('nan', '')
            df['전화번호_정제'] = df['전화번호_임시'].fillna('').astype(str).str.strip().replace('nan', '')
            all_dfs.append(df)
        except Exception as e:
            continue
    if not all_dfs: return pd.DataFrame()
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    def det_clear(row):
        g3, nm = str(row['품목그룹3']), str(row['상품명2']).upper()
        if ('투명' in g3 or '클리어' in nm) and '컬러' not in g3: return True
        return False
    combined_df['is_clear_lens'] = combined_df.apply(det_clear, axis=1)

    def m_ch(row):
        nm, g4 = str(row['상품명2']).upper(), str(row['품목그룹4']).upper()
        if '부대용품' in nm or '케이스' in nm or '액' in nm: return '기타'
        if '트루핏' in nm or 'PB' in g4: return 'PB'
        if '글로벌' in g4 or any(m in str(row['생산업체']) for m in ['존슨','바슈롬','알콘','쿠퍼']): return '글로벌'
        return 'OEM'
    combined_df['Custom_Channel'] = combined_df.apply(m_ch, axis=1)

    def m_pr(row):
        g1, nm = str(row['품목그룹1']), str(row['상품명2']).upper()
        if '부대용품' in nm: return '부대용품'
        if '토리카' in nm or '4만원' in g1: return '4만원 이상'
        if '악마' in nm or '클린핏' in nm: return '악마원데이'
        if '10P' in nm: return '원데이 10P'
        if row['is_clear_lens']: return '투명렌즈'
        if '2만5천원' in g1: return '25,000원'
        if '1만5천원' in g1: return '15,000원'
        if '1만원' in g1: return '10,000원'
        return '기타(미분류)'
    combined_df['Price_Type'] = combined_df.apply(m_pr, axis=1)
    combined_df['Color_Type'] = combined_df.apply(lambda r: '해당없음' if '기타' in r['Custom_Channel'] else ('투명' if r['is_clear_lens'] else '컬러'), axis=1)
    
    return combined_df

# (상권분석용 API 함수 - 카카오)
def search_location_by_kakao(query, key):
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    try:
        res = requests.get(url, headers={"Authorization": f"KakaoAK {key}"}, params={"query": query}, timeout=5)
        if res.status_code == 200 and res.json().get('documents'):
            docs = res.json()['documents'][0]
            return float(docs['y']), float(docs['x']), docs['place_name']
    except: pass
    return None, None, None

# (상권분석용 API 함수 - 소상공인)
@st.cache_data(ttl=3600)
def get_real_competitors(lat, lon, key):
    if not key or "여기에" in key: return None 
    url = "http://apis.data.go.kr/B553077/api/open/sdam/bizesInfoInRadius"
    try:
        res = requests.get(url, params={"ServiceKey": urllib.parse.unquote(key), "type": "json", "cy": lat, "cx": lon, "radius": 500, "numOfRows": 100}, timeout=5)
        if res.status_code == 200:
            stores = []
            for item in res.json().get('body', {}).get('items', []):
                name = item.get('bizesNm', '')
                if any(k in name for k in ['안경','렌즈','다비치','오렌즈']):
                    stores.append({'name': name, 'lat': float(item['lat']), 'lon': float(item['lon']), 'color': 'purple', 'icon': 'glasses', 'desc': item.get('indsSclsNm','')})
            return stores
    except: pass
    return None

# ==========================================
# 🚀 4. 사이드바 (앱 모드 선택 및 로그아웃)
# ==========================================
st.sidebar.markdown(f"**👤 접속중:** `{st.session_state.display_name}`")
if st.sidebar.button("🚪 로그아웃", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.user_id = ""
    st.session_state.display_name = ""
    st.rerun()

st.sidebar.markdown("---")
# 🌟 핵심: 프로그램 모드 스위치
app_mode = st.sidebar.radio("💻 프로그램 모드 선택", ["📊 1. 매장 실적 진단 (엑셀)", "🗺️ 2. 상권 이전 시뮬레이터"])
st.sidebar.markdown("---")

# ====================================================================================================
# [모드 1] 매장 실적 진단 (기존 엑셀 대시보드)
# ====================================================================================================
if app_mode == "📊 1. 매장 실적 진단 (엑셀)":
    st.sidebar.title("📁 매장 데이터 업로드")
    uploaded_files = st.sidebar.file_uploader("엑셀 파일 드래그", type=["xlsx", "xls"], accept_multiple_files=True)
    if uploaded_files:
        for file in uploaded_files:
            with open(os.path.join(USER_SAVE_DIR, file.name), "wb") as f: f.write(file.getbuffer())
        st.sidebar.success("✅ 파일 저장 완료!")

    saved_files = glob.glob(os.path.join(USER_SAVE_DIR, "*.xls*"))
    if saved_files and st.sidebar.button("🗑️ 내 저장된 파일 전체 삭제"):
        for f in saved_files: os.remove(f)
        st.rerun()

    if not saved_files:
        st.markdown(f"""<div style="text-align:center; margin-top:100px;"><h2>📊 환영합니다! {st.session_state.display_name}님</h2><p>좌측 메뉴에서 엑셀 파일을 업로드해 주세요.</p></div>""", unsafe_allow_html=True)
    else:
        df = load_data(saved_files)
        if df.empty:
            st.error("❌ 데이터 로드 실패")
            st.stop()
            
        compare_mode = st.sidebar.radio("🔍 분석 모드", ["단일 매장 조회", "단일 매장 기간 비교", "2개 이상 매장 비교"])
        st.sidebar.markdown("---")
        
        file_list = df['파일명'].unique().tolist()
        base_df = df[df['파일명'].isin(st.sidebar.multiselect("📄 분석 파일", file_list, default=file_list))]
        store_list = base_df['거래처(부서)'].unique().tolist()
        year_list = sorted([y for y in base_df['연도'].unique() if y != '연도미상'], reverse=True)
        month_list = [f"{i}월" for i in range(1, 13)]
        
        views, header_subtitle = [], ""

        if compare_mode == "단일 매장 조회":
            s_store = st.sidebar.selectbox("🏪 가맹점 선택", store_list)
            s_years = st.sidebar.multiselect("📅 연도", year_list, default=year_list)
            s_months = st.sidebar.multiselect("📅 월", month_list, default=[])
            p_ints = [int(m.replace('월', '')) for m in s_months]
            t_df = base_df[base_df['거래처(부서)'] == s_store]
            if s_years: t_df = t_df[t_df['연도'].isin(s_years)]
            if p_ints: t_df = t_df[t_df['월'].isin(p_ints)]
            header_subtitle = f"단일 매장 조회 | {s_store}"
            views.append({"title": f"🏪 {s_store} 실적", "df": t_df})

        elif compare_mode == "단일 매장 기간 비교":
            s_store = st.sidebar.selectbox("🏪 가맹점", store_list)
            p1_y = st.sidebar.multiselect("🔹 기준 연도", year_list, default=[year_list[-1]] if year_list else [])
            p1_m = st.sidebar.multiselect("🔹 기준 월", month_list, default=["1월", "2월", "3월"])
            p2_y = st.sidebar.multiselect("🔸 비교 연도", year_list, default=[year_list[0]] if year_list else [])
            p2_m = st.sidebar.multiselect("🔸 비교 월", month_list, default=["1월", "2월", "3월"])
            
            store_df = base_df[base_df['거래처(부서)'] == s_store]
            v1_df, v2_df = store_df.copy(), store_df.copy()
            
            if p1_y: v1_df = v1_df[v1_df['연도'].isin(p1_y)]
            if p1_m: v1_df = v1_df[v1_df['월'].isin([int(m.replace('월','')) for m in p1_m])]
            if p2_y: v2_df = v2_df[v2_df['연도'].isin(p2_y)]
            if p2_m: v2_df = v2_df[v2_df['월'].isin([int(m.replace('월','')) for m in p2_m])]
            header_subtitle = f"기간 비교 | {s_store}"
            views.append({"title": f"[{s_store}] 기준기간", "df": v1_df})
            views.append({"title": f"[{s_store}] 비교기간", "df": v2_df})

        else:
            s_stores = st.sidebar.multiselect("🏪 비교 가맹점", store_list, default=store_list[:2] if store_list else [])
            t_df = base_df
            header_subtitle = f"다중 매장 비교"
            for store in s_stores:
                views.append({"title": f"🏪 {store}", "df": t_df[t_df['거래처(부서)'] == store]})

        st.sidebar.markdown("---")
        s_chan = st.sidebar.multiselect("📦 브랜드", ['OEM', 'PB', '글로벌', '기타'], default=[])
        s_col = st.sidebar.multiselect("👁️ 렌즈 종류", ['컬러', '투명'], default=[])
        
        for v in views:
            if s_chan: v['df'] = v['df'][v['df']['Custom_Channel'].isin(s_chan)]
            if s_col: v['df'] = v['df'][v['df']['Color_Type'].isin(s_col)]

        st.markdown(f"""<div class="header-banner"><div class="header-title">렌즈미 매장 매출 진단 리포트</div><div class="header-subtitle">{header_subtitle}</div></div>""", unsafe_allow_html=True)
        tab_sales, tab_cust, tab_rnw = st.tabs(["📊 매출데이터", "👥 고객데이터", "✨ 리뉴얼"])

        with tab_sales:
            chk_col1, chk_col2, chk_col3 = st.columns(3)
            show_s = chk_col1.checkbox("✅ 매출액 차트", value=True)
            show_m = chk_col3.checkbox("✅ 마진율 차트", value=False)
            
            view_cols = st.columns(len(views)) if views else st.columns(1)
            for idx, view in enumerate(views):
                with view_cols[idx]:
                    st.markdown(f"<h3 style='text-align:center; border-bottom:3px solid #4f46e5;'>{view['title']}</h3>", unsafe_allow_html=True)
                    v_df = view['df']
                    if v_df.empty: continue
                    t_sales = v_df['금액'].sum()
                    t_rec = v_df['전표번호'].nunique()
                    l_df = v_df[v_df['Custom_Channel'] != '기타']
                    m_rate = (l_df['총마진'].sum() / l_df['금액'].sum() * 100) if l_df['금액'].sum() > 0 else 0
                    
                    c1, c2 = st.columns(2)
                    with c1: st.markdown(f'<div class="metric-card border-indigo"><div class="metric-label">총매출</div><div class="metric-value">{int(t_sales):,}원</div></div>', unsafe_allow_html=True)
                    with c2: st.markdown(f'<div class="metric-card border-pink"><div class="metric-label">마진율</div><div class="metric-value">{m_rate:.1f}%</div></div>', unsafe_allow_html=True)
                    
                    if show_s:
                        d_bar = v_df.groupby('Custom_Channel')['금액'].sum().reset_index()
                        fig = px.bar(d_bar, x='Custom_Channel', y='금액', text='금액', color='Custom_Channel', color_discrete_map=CATEGORY_COLORS)
                        fig.update_traces(texttemplate='<b>%{text:,.0f}원</b>', textposition='outside')
                        fig.update_layout(showlegend=False, xaxis_title="")
                        st.plotly_chart(fig, use_container_width=True)

        with tab_cust:
            st.info("고객 재방문율 및 구매 리스트 데이터 공간입니다.")

        with tab_rnw:
            st.markdown("### ✨ 매장 리뉴얼 및 인테리어")
            s_type = st.radio("분류", ["🏢 단독샵", "🏪 샵인샵"], horizontal=True, label_visibility="collapsed")
            folder = os.path.join("images", "standalone" if s_type=="🏢 단독샵" else "shopinshop")
            imgs = glob.glob(os.path.join(folder, "*.jpg")) + glob.glob(os.path.join(folder, "*.png"))
            if imgs:
                cols = st.columns(3)
                for i, img in enumerate(imgs): cols[i%3].image(img, use_container_width=True)
            else: st.info("폴더에 등록된 사진이 없습니다.")

# ====================================================================================================
# [모드 2] 상권 이전 시뮬레이터 (지도 및 ROI 분석)
# ====================================================================================================
elif app_mode == "🗺️ 2. 상권 이전 시뮬레이터":
    st.sidebar.title("🔍 상권 통합 검색")
    search_query = st.sidebar.text_input("📍 위치 검색 (예: 서면 올리브영, 강남역)")
    
    if st.sidebar.button("🚀 지도로 이동하기", use_container_width=True):
        if search_query:
            lat, lon, p_name = search_location_by_kakao(search_query, KAKAO_REST_API_KEY)
            if lat and lon:
                st.session_state.center_lat = lat
                st.session_state.center_lon = lon
                st.session_state.candidate_store = p_name
                st.rerun()
            else: st.sidebar.error("검색 결과를 찾을 수 없습니다. (띄어쓰기를 다르게 해보시거나 건물명으로 검색해보세요.)")

    st.sidebar.markdown("---")
    current_store = st.sidebar.text_input("현재 매장명", value="렌즈미 천안쌍용점")
    st.sidebar.text_input("분석 상권(목적지)", value=st.session_state.candidate_store, disabled=True)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 지도 표시 필터")
    show_olens = st.sidebar.checkbox("🟠 오렌즈", value=True)
    show_davich = st.sidebar.checkbox("🔵 다비치", value=True)

    st.markdown(f'<div class="header-banner"><div class="header-title">렌즈미 상권 분석 및 이전 시뮬레이터</div><div class="header-subtitle">선택된 상권: {st.session_state.candidate_store}</div></div>', unsafe_allow_html=True)
    
    tab_map, tab_pop, tab_radar, tab_roi = st.tabs(["📍 지도 & 경쟁사", "👥 유동인구", "📊 입지 비교", "💰 ROI 시뮬레이터"])

    with tab_map:
        m = folium.Map(location=[st.session_state.center_lat, st.session_state.center_lon], zoom_start=16, tiles=None)
        folium.TileLayer(tiles='http://mt0.google.com/vt/lyrs=m&hl=ko&x={x}&y={y}&z={z}', attr='Google', name='Google').add_to(m)
        plugins.Fullscreen(position='topright').add_to(m)
        
        folium.Marker([st.session_state.center_lat, st.session_state.center_lon], popup=f"<b>{st.session_state.candidate_store}</b>", icon=folium.Icon(color="red", icon="star", prefix='fa')).add_to(m)
        folium.Circle(radius=500, location=[st.session_state.center_lat, st.session_state.center_lon], color="#4f46e5", fill=True, fill_opacity=0.15).add_to(m)
        
        comps = get_real_competitors(st.session_state.center_lat, st.session_state.center_lon, DATA_GO_KR_API_KEY)
        if comps is None:
            st.warning("⚠️ 소상공인 API 키 미입력 시 경쟁사(안경원) 마커는 샘플로만 표시됩니다.")
            comps = [{"name": "오렌즈(샘플)", "lat": st.session_state.center_lat+0.001, "lon": st.session_state.center_lon-0.001, "color":"orange"}]
        
        for c in comps:
            folium.Marker([c["lat"], c["lon"]], tooltip=c["name"], icon=folium.Icon(color=c.get("color","purple"), icon="glasses", prefix='fa')).add_to(m)
            
        st_folium(m, width="100%", height=600)

    with tab_pop:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown('<div class="metric-box"><div class="metric-title">일평균 유동인구</div><div class="metric-value">28,450명</div></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="metric-box"><div class="metric-title">여성 비율</div><div class="metric-value" style="color:#ec4899;">58.2%</div></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="metric-box"><div class="metric-title">1020 타겟 비율</div><div class="metric-value" style="color:#4f46e5;">42.5%</div></div>', unsafe_allow_html=True)
        with c4: st.markdown('<div class="metric-box"><div class="metric-title">혼잡 시간대</div><div class="metric-value">16시 ~ 20시</div></div>', unsafe_allow_html=True)

        cc1, cc2 = st.columns(2)
        with cc1:
            fig_age = px.pie(pd.DataFrame({'연령': ['10대', '20대', '30대', '40대'], '수': [4200, 7800, 6500, 5100]}), values='수', names='연령', hole=0.4, title="연령대 비중")
            st.plotly_chart(fig_age, use_container_width=True)
        with cc2:
            fig_t = px.line(pd.DataFrame({'시간': ['09시', '12시', '15시', '18시'], '수': [1800, 5200, 8900, 7100]}), x='시간', y='수', title="시간대별 유동인구")
            st.plotly_chart(fig_t, use_container_width=True)

    with tab_radar:
        col1, col2 = st.columns([1, 2])
        with col1: st.markdown(f"**현재:** {current_store}<br>**후보:** {st.session_state.candidate_store}", unsafe_allow_html=True)
        with col2:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=[60, 55, 80, 70, 50, 60], theta=['유동인구','타겟밀집','경쟁','임대료','활력도','유동인구'], fill='toself', name=current_store))
            fig.add_trace(go.Scatterpolar(r=[90, 85, 40, 65, 95, 90], theta=['유동인구','타겟밀집','경쟁','임대료','활력도','유동인구'], fill='toself', name=st.session_state.candidate_store))
            st.plotly_chart(fig, use_container_width=True)

    with tab_roi:
        ci, cr = st.columns([1, 1.5])
        with ci:
            dep = st.number_input("보증금(만)", 5000)
            pre = st.number_input("권리금(만)", 3000)
            int_c = st.number_input("인테리어(만)", 6000)
            daily_c = st.slider("일평균 고객", 10, 150, 40)
            atv = st.slider("객단가(만)", 2.0, 8.0, 3.5)
            mar = st.slider("마진율(%)", 30, 70, 45)
            rent = st.number_input("월세(만)", 300)
            labor = st.number_input("인건비/기타(만)", 400)
        with cr:
            net_profit = (daily_c * atv * 30 * (mar/100)) - rent - labor
            sunk = pre + int_c
            payback = sunk / net_profit if net_profit > 0 else 0
            
            mc1, mc2, mc3 = st.columns(3)
            mc1.markdown(f'<div class="metric-box"><div class="metric-title">총 투자</div><div class="metric-value">{dep+pre+int_c:,}만</div></div>', unsafe_allow_html=True)
            mc2.markdown(f'<div class="metric-box"><div class="metric-title">월 순수익</div><div class="metric-value">{int(net_profit):,}만</div></div>', unsafe_allow_html=True)
            mc3.markdown(f'<div class="metric-box"><div class="metric-title">회수기간</div><div class="metric-value">{f"{payback:.1f}개월" if payback>0 else "불가"}</div></div>', unsafe_allow_html=True)
            
            if net_profit > 0:
                df_roi = pd.DataFrame({'월': range(1,25), '누적수익': [(net_profit*m)-sunk for m in range(1,25)]})
                fig_bar = px.bar(df_roi, x='월', y='누적수익', title="2년 누적 수익 예측", color='누적수익', color_continuous_scale=px.colors.diverging.RdYlGn)
                st.plotly_chart(fig_bar, use_container_width=True)
