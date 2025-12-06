"""
Hệ Thống Phân Tích Danh Mục Multi-Alpha
=======================================
Giao diện chuyên nghiệp, bảng màu Deep Navy & Charcoal
Toàn bộ bằng tiếng Việt trừ keyword chuyên ngành
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import modules
from chat_assistant import chat_tab
from signal_analysis import display_signal_analysis_tab
from metrics_config import (
    METRICS_CONFIG, CATEGORY_NAMES, CATEGORY_DESCRIPTIONS,
    evaluate_metric, format_metric_value, get_metric_config
)

# Cấu hình trang
st.set_page_config(
    page_title="Phân Tích Danh Mục Multi-Alpha",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS chuyên nghiệp - Màu Deep Navy & Charcoal
st.markdown("""
<style>
    /* Import font chuyên nghiệp */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap');
    
    /* Style toàn cục */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Container chính */
    .main {
        background-color: #fafafa;
        padding: 2rem;
    }
    
    /* Tiêu đề */
    h1 {
        color: #1a237e;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }
    
    h2 {
        color: #263238;
        font-weight: 600;
        font-size: 1.5rem;
        border-bottom: 2px solid #1a237e;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    
    h3 {
        color: #37474f;
        font-weight: 500;
        font-size: 1.2rem;
    }
    
    /* Thẻ chỉ số */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f5f5f5 100%);
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    .metric-label {
        color: #757575;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        color: #1a237e;
        font-size: 2rem;
        font-weight: 700;
        font-family: 'Roboto Mono', monospace;
    }
    
    .metric-rating {
        font-size: 0.8rem;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 0.5rem;
    }
    
    .rating-excellent {
        background-color: #e8f5e9;
        color: #2e7d32;
    }
    
    .rating-good {
        background-color: #e3f2fd;
        color: #1565c0;
    }
    
    .rating-warning {
        background-color: #fff3e0;
        color: #e65100;
    }
    
    .rating-poor {
        background-color: #ffebee;
        color: #c62828;
    }
    
    /* Thẻ điểm chữ */
    .grade-card {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        color: white;
    }
    
    .grade-letter {
        font-size: 4rem;
        font-weight: 700;
        margin: 0;
    }
    
    .grade-description {
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #263238;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f5f5f5;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1a237e;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ==================== HÀM TRỢ GIÚP ====================

def tai_tat_ca_du_lieu(thu_muc_ket_qua):
    """Tải tất cả dữ liệu kết quả"""
    du_lieu = {
        'tom_tat': None,
        'equity': {},
        'ket_qua': {},
        'giao_dich': {},
        'signals': {}  # Added for signal_analysis compatibility
    }
    
    # Tải báo cáo tổng kết
    file_bao_cao = os.path.join(thu_muc_ket_qua, 'Final_Report.csv')
    if os.path.exists(file_bao_cao):
        du_lieu['tom_tat'] = pd.read_csv(file_bao_cao)
    
    # Tải từng loại file
    for file in os.listdir(thu_muc_ket_qua):
        if file.endswith('.csv'):
            duong_dan = os.path.join(thu_muc_ket_qua, file)
            ten_cluster = file.replace('.csv', '')
            
            if file.startswith('equity_'):
                ten_cluster = ten_cluster.replace('equity_', '')
                df = pd.read_csv(duong_dan, index_col=0, parse_dates=True)
                du_lieu['equity'][ten_cluster] = df
            elif file.startswith('result_'):
                ten_cluster = ten_cluster.replace('result_', '')
                du_lieu['ket_qua'][ten_cluster] = pd.read_csv(duong_dan, index_col=0, parse_dates=True)
            elif file.startswith('trades_'):
                ten_cluster = ten_cluster.replace('trades_', '')
                du_lieu['giao_dich'][ten_cluster] = pd.read_csv(duong_dan)
            elif file.startswith('signals_'):
                ten_cluster = ten_cluster.replace('signals_', '')
                du_lieu['signals'][ten_cluster] = pd.read_csv(duong_dan, index_col=0, parse_dates=True)
    
    return du_lieu


def danh_gia_mo_hinh(du_lieu):
    """Đánh giá tổng thể mô hình với điểm chữ"""
    if du_lieu['tom_tat'] is None:
        return None
    
    tom_tat = du_lieu['tom_tat'].iloc[0]
    sharpe = tom_tat['Sharpe_Ratio']
    cagr = tom_tat['Annual_Return_CAGR']
    max_dd = abs(tom_tat['Max_Drawdown'])
    win_rate = tom_tat['Win_Rate']
    
    # Tính điểm dựa trên từng chỉ số
    diem = 0
    
    # Sharpe (0-40 điểm)
    if sharpe >= 2.0:
        diem += 40
    elif sharpe >= 1.5:
        diem += 35
    elif sharpe >= 1.0:
        diem += 25
    elif sharpe >= 0.5:
        diem += 15
    else:
        diem += 5
    
    # CAGR (0-30 điểm)
    if cagr >= 0.30:
        diem += 30
    elif cagr >= 0.20:
        diem += 25
    elif cagr >= 0.10:
        diem += 15
    else:
        diem += 5
    
    # Max DD (0-20 điểm) - càng nhỏ càng tốt
    if max_dd <= 0.20:
        diem += 20
    elif max_dd <= 0.30:
        diem += 15
    elif max_dd <= 0.40:
        diem += 10
    else:
        diem += 5
    
    # Win Rate (0-10 điểm)
    if win_rate >= 0.55:
        diem += 10
    elif win_rate >= 0.50:
        diem += 7
    else:
        diem += 3
    
    # Xác định điểm chữ
    if diem >= 90:
        diem_chu = 'A+'
        chat_luong = 'Xuất sắc'
        loai_ndt = 'Tổ chức'
    elif diem >= 80:
        diem_chu = 'A'
        chat_luong = 'Tuyệt vời'
        loai_ndt = 'Tổ chức'
    elif diem >= 70:
        diem_chu = 'B+'
        chat_luong = 'Rất tốt'
        loai_ndt = 'Chuyên nghiệp'
    elif diem >= 60:
        diem_chu = 'B'
        chat_luong = 'Tốt'
        loai_ndt = 'Bán lẻ nâng cao'
    elif diem >= 50:
        diem_chu = 'C'
        chat_luong = 'Trung bình'
        loai_ndt = 'Bán lẻ'
    else:
        diem_chu = 'D'
        chat_luong = 'Cần cải thiện'
        loai_ndt = 'Chỉ nghiên cứu'
    
    return {
        'diem': diem,
        'diem_chu': diem_chu,
        'chat_luong': chat_luong,
        'loai_ndt': loai_ndt,
        'sharpe': sharpe,
        'cagr': cagr,
        'max_dd': tom_tat['Max_Drawdown'],
        'win_rate': win_rate,
        'vuot_sp500_loi_nhuan': (cagr - 0.10) * 100
    }


def tao_bieu_do_chuyen_nghiep(df, tieu_de, cot_y):
    """Tạo biểu đồ chuyên nghiệp với style Deep Navy"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df[cot_y],
        mode='lines',
        name=tieu_de,
        line=dict(color='#1a237e', width=2),
        fill='tozeroy',
        fillcolor='rgba(26, 35, 126, 0.1)'
    ))
    
    fig.update_layout(
        title=dict(
            text=tieu_de,
            font=dict(size=16, color='#263238', family='Inter')
        ),
        xaxis=dict(
            title='Ngày',
            showgrid=True,
            gridcolor='#e0e0e0',
            linecolor='#bdbdbd'
        ),
        yaxis=dict(
            title='Phần trăm (%)',
            showgrid=True,
            gridcolor='#e0e0e0',
            linecolor='#bdbdbd',
            tickformat='.1f',
            ticksuffix='%'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Inter'),
        hovermode='x unified',
        height=400,
        margin=dict(l=60, r=20, t=60, b=40)
    )
    
    return fig


def hien_thi_chi_so_gon(col, nhan, gia_tri, xep_hang="Tốt", hau_to=""):
    """Hiển thị thẻ chỉ số gọn gàng không icon"""
    mau_xep_hang = {
        "Xuất sắc": "rating-excellent",
        "Tuyệt vời": "rating-excellent",
        "Rất tốt": "rating-good",
        "Tốt": "rating-good",
        "Trung bình": "rating-warning",
        "Kém": "rating-poor"
    }
    
    css_class = mau_xep_hang.get(xep_hang, "rating-good")
    
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{nhan}</div>
        <div class="metric-value">{gia_tri}{hau_to}</div>
        <div class="metric-rating {css_class}">{xep_hang}</div>
    </div>
    """, unsafe_allow_html=True)


# ==================== ỨNG DỤNG CHÍNH ====================

def main():
    # Tiêu đề
    st.markdown('<h1>Phân Tích Danh Mục Multi-Alpha</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #757575; font-size: 1rem; margin-top: -0.5rem;">Hệ Thống Giao Dịch Định Lượng Chuyên Nghiệp</p>', unsafe_allow_html=True)
    
    # Sidebar TRƯỚC (đặt đường dẫn kết quả)
    with st.sidebar:
        st.markdown("### Tổng Quan Hệ Thống")
        
        # Chọn kịch bản
        st.markdown("---")
        st.markdown("### Chọn Kịch Bản")
        kich_ban = st.selectbox(
            "Chọn kịch bản backtest:",
            [
                "Kịch bản 1: Tất cả 6 Cluster (Không RM)",
                "Kịch bản 2: 3 Cluster đã lọc",
                "Kịch bản 3: Có Risk Management"
            ],
            help="""
            - Kịch bản 1: Tất cả cluster, 100% exposure, không lọc
            - Kịch bản 2: Chỉ 3 cluster tốt (Banks/Consumer/Tech SW)
            - Kịch bản 3: Risk management bật (70% exposure, tối thiểu 4 cổ phiếu)
            """
        )
        
        # Map lựa chọn sang thư mục
        ban_do_kich_ban = {
            "Kịch bản 1: Tất cả 6 Cluster (Không RM)": "MultiAlpha_Results_Scenario1",
            "Kịch bản 2: 3 Cluster đã lọc": "MultiAlpha_Results_Scenario2", 
            "Kịch bản 3: Có Risk Management": "MultiAlpha_Results_Scenario3"
        }
        
        thu_muc_chon = ban_do_kich_ban[kich_ban]
        
        # Sử dụng đường dẫn tương đối từ vị trí app.py
        thu_muc_goc = Path(__file__).parent.parent.parent / "apply_strategy"
        thu_muc_ket_qua = str(thu_muc_goc / thu_muc_chon)
        
        # Hiển thị thông tin kịch bản
        if "Kịch bản 1" in kich_ban:
            st.info("6 cluster, Sharpe trung bình 0.49")
        elif "Kịch bản 2" in kich_ban:
            st.success("3 cluster, Sharpe trung bình 0.78")
        else:
            st.warning("1 cluster, Sharpe 1.17")
        
        st.markdown("---")
        st.metric("Số kịch bản có sẵn", "3")
    
    # BÂY GIỜ tải dữ liệu sử dụng thu_muc_ket_qua từ sidebar
    if not os.path.exists(thu_muc_ket_qua):
        st.error(f"Không tìm thấy thư mục kết quả: {thu_muc_ket_qua}")
        return
    
    with st.spinner(f'Đang tải {kich_ban}...'):
        du_lieu = tai_tat_ca_du_lieu(thu_muc_ket_qua)
    
    if du_lieu['tom_tat'] is None:
        st.error("Không có dữ liệu")
        return
    
    # Các tab chính
    tabs = st.tabs([
        "Đánh Giá Mô Hình",
        "Hiệu Suất Danh Mục",
        "Tín Hiệu Giao Dịch",
        "Trợ Lý AI"
    ])
    
    # TAB 1: ĐÁNH GIÁ MÔ HÌNH
    with tabs[0]:
        st.markdown('<h2>Đánh Giá Mô Hình</h2>', unsafe_allow_html=True)
        
        ket_qua_dg = danh_gia_mo_hinh(du_lieu)
        
        if ket_qua_dg:
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.markdown(f"""
                <div class="grade-card">
                    <div class="metric-label" style="color: rgba(255,255,255,0.7);">Điểm Tổng Thể</div>
                    <div class="grade-letter">{ket_qua_dg['diem_chu']}</div>
                    <div class="grade-description">{ket_qua_dg['chat_luong']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-label">Điểm Số</div>
                    <div class="metric-value">{ket_qua_dg['diem']}/100</div>
                    <div class="metric-rating rating-good">Điểm tổng hợp</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div class="metric-label">Loại Nhà Đầu Tư</div>
                    <div class="metric-value" style="font-size: 1.5rem;">{ket_qua_dg['loai_ndt']}</div>
                    <div class="metric-rating rating-good">Phù hợp cho</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # So sánh với benchmark
            st.markdown('<h3>So Sánh Với Benchmark</h3>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            hien_thi_chi_so_gon(col1, "Sharpe Ratio", f"{ket_qua_dg['sharpe']:.2f}", ket_qua_dg['chat_luong'])
            hien_thi_chi_so_gon(col2, "Lợi Nhuận Hàng Năm", f"{ket_qua_dg['cagr']*100:.1f}", "Xuất sắc", "%")
            hien_thi_chi_so_gon(col3, "So với S&P500", f"+{ket_qua_dg['vuot_sp500_loi_nhuan']:.1f}", "Xuất sắc", "%")
            hien_thi_chi_so_gon(col4, "Sụt Giảm Tối Đa", f"{ket_qua_dg['max_dd']*100:.1f}", "Tốt", "%")
    
    # TAB 2: HIỆU SUẤT DANH MỤC
    with tabs[1]:
        st.markdown('<h2>Phân Tích Hiệu Suất Danh Mục</h2>', unsafe_allow_html=True)
        
        # Lấy dữ liệu cluster
        cluster = list(du_lieu['equity'].keys())[0]
        df_equity = du_lieu['equity'][cluster]
        tom_tat = du_lieu['tom_tat'].iloc[0]
        
        # === PHẦN 1: TỔNG QUAN CHỈ SỐ CHÍNH ===
        st.markdown("### Các Chỉ Số Hiệu Suất Chính")
        
        col1, col2, col3, col4 = st.columns(4)
        
        sharpe = tom_tat['Sharpe_Ratio']
        tong_ln = tom_tat['Total_Return'] * 100
        max_dd = tom_tat['Max_Drawdown'] * 100
        ty_le_thang = tom_tat['Win_Rate'] * 100
        
        with col1:
            st.metric("Sharpe Ratio", f"{sharpe:.2f}")
            if sharpe > 1.5:
                st.success("🌟 Xuất sắc - Cấp độ tổ chức")
            elif sharpe > 1.0:
                st.success("✅ Tốt - Trên trung bình")
            elif sharpe > 0.5:
                st.info("⚠️ Chấp nhận được - Dưới mục tiêu")
            else:
                st.error("❌ Kém - Cần cải thiện")
        
        with col2:
            st.metric("Tổng Lợi Nhuận", f"{tong_ln:.1f}%")
            if tong_ln > 1000:
                st.success("🚀 Hiệu suất xuất sắc")
            elif tong_ln > 300:
                st.success("✅ Lợi nhuận mạnh")
            else:
                st.info("📊 Tăng trưởng vừa phải")
        
        with col3:
            st.metric("Sụt Giảm Tối Đa", f"{max_dd:.1f}%")
            if abs(max_dd) < 30:
                st.success("✅ Kiểm soát tốt")
            elif abs(max_dd) < 50:
                st.warning("⚠️ Rủi ro trung bình")
            else:
                st.error("📉 Rủi ro cao - Cần xem xét")
        
        with col4:
            st.metric("Tỷ Lệ Thắng", f"{ty_le_thang:.1f}%")
            if ty_le_thang > 55:
                st.success("🎯 Sinh lời ổn định")
            elif ty_le_thang > 50:
                st.info("✅ Có lợi thế nhỏ")
            else:
                st.warning("⚠️ Cần độ chính xác cao hơn")
        
        st.markdown("---")
        
        # === PHẦN 2: PHÂN TÍCH CHI TIẾT ===
        st.markdown("### 📊 Phân Tích & Diễn Giải Hiệu Suất")
        
        # Phân tích hiệu suất điều chỉnh rủi ro
        with st.expander("🎯 Phân Tích Hiệu Suất Điều Chỉnh Rủi Ro", expanded=True):
            st.markdown(f"""
            **Sharpe Ratio: {sharpe:.2f}**
            
            **Ý nghĩa:**
            - Đo lường lợi nhuận trên mỗi đơn vị rủi ro
            - Sharpe > 1.0 được coi là tốt cho chiến lược định lượng
            - Sharpe của bạn là {sharpe:.2f} - {'**xuất sắc**' if sharpe > 1.5 else '**tốt**' if sharpe > 1.0 else 'chấp nhận được'}
            
            **Diễn giải:**
            """)
            
            if sharpe > 1.5:
                st.success("""
                ✅ **Hiệu suất cấp độ tổ chức**  
                - Chiến lược mang lại lợi nhuận điều chỉnh rủi ro xuất sắc
                - Tương đương với các quỹ hedge fund hàng đầu (mục tiêu: Sharpe > 1.5)
                - Ứng viên sáng giá để triển khai thực tế
                - Dự kiến vượt trội 90%+ người tham gia thị trường
                """)
            elif sharpe > 1.0:
                st.info("""
                ✅ **Hiệu suất trên trung bình**  
                - Chiến lược có quản lý rủi ro tốt
                - Vượt trội so với buy-and-hold thông thường (Sharpe ~0.5)
                - Còn dư địa cải thiện thông qua giảm DD
                - Cân nhắc áp dụng volatility targeting
                """)
            else:
                st.warning("""
                ⚠️ **Cần tối ưu hóa**  
                - Lợi nhuận chưa xứng đáng với rủi ro
                - Xem lại chất lượng tín hiệu và cách kết hợp
                - Áp dụng quản lý rủi ro nghiêm ngặt hơn
                - Cân nhắc đa dạng hóa danh mục
                """)
            
            # So sánh Sortino Ratio
            sortino = tom_tat.get('Sortino_Ratio', sharpe * 1.2)
            st.markdown(f"""
            **Sortino Ratio: {sortino:.2f}** (so với Sharpe {sharpe:.2f})
            - Sortino chỉ phạt biến động chiều giảm (downside)
            - Sortino cao hơn cho thấy lợi nhuận không đối xứng (tốt!)
            - Tỷ lệ {sortino/sharpe:.2f}x cho thấy {'xu hướng tăng mạnh ✅' if sortino/sharpe > 1.15 else 'phân phối cân bằng'}
            """)
        
        # Phân tích lợi nhuận
        with st.expander("💰 Phân Tích Sinh Lời"):
            cagr = tom_tat['Annual_Return_CAGR'] * 100
            so_nam = tom_tat['Trading_Years']
            
            st.markdown(f"""
            **Tổng Lợi Nhuận: {tong_ln:.1f}%** trong {so_nam:.1f} năm  
            **CAGR: {cagr:.1f}%** mỗi năm
            
            **So Sánh Benchmark:**
            - CAGR lịch sử S&P 500: ~10%
            - CAGR của bạn: {cagr:.1f}%
            - **Vượt trội: +{cagr-10:.1f}% hàng năm** {'🚀' if cagr > 30 else '✅' if cagr > 15 else ''}
            
            **Điều này có nghĩa:**
            """)
            
            if cagr > 40:
                st.success(f"""
                🚀 **Sinh lời xuất sắc**  
                - CAGR {cagr:.1f}% rất hiếm (top 1% chiến lược)
                - $10,000 → ${10000 * (1 + cagr/100)**so_nam:,.0f} trong {so_nam:.0f} năm
                - Vượt trội hầu hết các quỹ chuyên nghiệp
                - **Hành động:** Đảm bảo lợi nhuận bền vững, không phải curve-fitting
                """)
            elif cagr > 20:
                st.success(f"""
                ✅ **Hiệu suất mạnh**  
                - CAGR {cagr:.1f}% vượt mục tiêu tổ chức (15-20%)
                - $10,000 → ${10000 * (1 + cagr/100)**so_nam:,.0f} trong {so_nam:.0f} năm
                - Tương đương với các quỹ quant thành công
                - **Hành động:** Sẵn sàng triển khai vốn từ từ
                """)
            else:
                st.info(f"""
                📊 **Lợi nhuận vừa phải**  
                - CAGR {cagr:.1f}% vượt S&P500 nhưng còn dư địa cải thiện
                - Cân nhắc tăng alpha hoặc sử dụng đòn bẩy
                - Có thể phù hợp với nhà đầu tư thận trọng
                """)
        
        # Phân tích rủi ro
        with st.expander("📉 Phân Tích Sụt Giảm & Rủi Ro"):
            dd_tb = tom_tat['Avg_Drawdown'] * 100
            calmar = tom_tat.get('Calmar_Ratio', cagr / abs(max_dd) * 100)
            
            st.markdown(f"""
            **Sụt Giảm Tối Đa: {max_dd:.1f}%**  
            **Sụt Giảm Trung Bình: {dd_tb:.1f}%**  
            **Calmar Ratio: {calmar:.2f}** (CAGR / Max DD)
            
            **Đánh Giá Rủi Ro:**
            """)
            
            if abs(max_dd) < 30:
                st.success("""
                ✅ **Kiểm soát rủi ro xuất sắc**  
                - Max DD < 30% là ngoại lệ cho chiến lược quant
                - Xác suất thua lỗ nghiêm trọng thấp
                - Phù hợp cho vốn tổ chức
                - **Tâm lý:** Dễ dàng giữ vững qua các đợt sụt giảm
                """)
            elif abs(max_dd) < 50:
                st.warning(f"""
                ⚠️ **Mức độ rủi ro trung bình**  
                - Max DD {abs(max_dd):.1f}% là điển hình cho chiến lược quant
                - Lập kế hoạch cho tình huống xấu nhất: -50% đến -60% có thể xảy ra
                - **Chiến lược giảm thiểu:**
                  - Áp dụng đặt kích thước vị thế động
                  - Thêm stop-loss tại -30% DD
                  - Sử dụng volatility targeting
                - **Thời gian phục hồi dự kiến:** 3-6 tháng dựa trên CAGR
                """)
            else:
                st.error("""
                📉 **Rủi ro cao - Cần hành động**  
                - Drawdown > 50% rất khó chịu về mặt tâm lý
                - Hầu hết nhà đầu tư bỏ cuộc ở mức -40% đến -50%
                - **Hành động ngay:**
                  1. Giảm kích thước vị thế 30-50%
                  2. Áp dụng circuit breaker
                  3. Xem lại chất lượng tín hiệu trong giai đoạn sụt giảm
                  4. Cân nhắc bộ lọc regime thị trường
                """)
            
            st.markdown(f"""
            **Diễn Giải Calmar Ratio:**
            - Calmar {calmar:.2f} nghĩa là bạn kiếm {calmar:.1f}% hàng năm mỗi 1% max DD
            - {'Xuất sắc' if calmar > 1.0 else 'Tốt' if calmar > 0.5 else 'Cần cải thiện'} (mục tiêu > 0.5)
            """)
        
        # Chất lượng giao dịch
        with st.expander("🎲 Chất Lượng & Tính Nhất Quán Giao Dịch"):
            profit_factor = tom_tat.get('Profit_Factor', 1.3)
            ty_le_ln_lo = tom_tat.get('Win_Loss_Ratio', 1.1)
            
            st.markdown(f"""
            **Tỷ Lệ Thắng: {ty_le_thang:.1f}%**  
            **Profit Factor: {profit_factor:.2f}**  
            **Tỷ Lệ Lãi/Lỗ: {ty_le_ln_lo:.2f}**
            
            **Các chỉ số này cho thấy:**
            """)
            
            st.markdown(f"""
            **Phân Tích Tỷ Lệ Thắng:**
            - {ty_le_thang:.1f}% giao dịch có lãi
            - {'Chiến lược độ chính xác cao ✅' if ty_le_thang > 55 else 'Cách tiếp cận cân bằng' if ty_le_thang > 45 else 'Tỷ lệ thắng thấp ⚠️'}
            - {100 - ty_le_thang:.1f}% là thua lỗ (bình thường cho mean-reversion)
            
            **Profit Factor: {profit_factor:.2f}**
            - Tỷ lệ Tổng Lãi / Tổng Lỗ
            - {profit_factor:.2f} nghĩa là bạn kiếm ${profit_factor:.2f} cho mỗi $1 thua
            """)
            
            if profit_factor > 1.5:
                st.success("🌟 Xuất sắc - Giao dịch thắng lớn hơn đáng kể")
            elif profit_factor > 1.2:
                st.success("✅ Tốt - Bền vững về dài hạn")
            elif profit_factor > 1.0:
                st.warning("⚠️ Biên lợi nhuận mỏng - Rủi ro chi phí giao dịch cao")
            else:
                st.error("❌ Chiến lược thua lỗ - Cần xem xét ngay")
            
            st.markdown(f"""
            **Tỷ Lệ Lãi/Lỗ: {ty_le_ln_lo:.2f}**
            - Lãi trung bình gấp {ty_le_ln_lo:.2f}x lỗ trung bình
            - {'Payoff không đối xứng - lý tưởng ✅' if ty_le_ln_lo > 1.5 else 'Lãi/lỗ cân bằng' if ty_le_ln_lo > 0.8 else 'Lỗ lớn hơn lãi ⚠️'}
            
            **Insight Triết Lý Giao Dịch:**
            """)
            
            if ty_le_thang > 55 and ty_le_ln_lo > 1.0:
                st.success("""
                💎 **Tỷ lệ thắng cao + Payoff dương = Sự kết hợp lý tưởng**  
                - Bạn thắng thường xuyên VÀ thắng lớn
                - Hiếm trong giao dịch định lượng
                - Cho thấy chất lượng tín hiệu mạnh
                """)
            elif ty_le_thang < 50 and ty_le_ln_lo > 1.5:
                st.info("""
                🎯 **Hồ sơ trend-following điển hình**  
                - Nhiều thua lỗ nhỏ, ít thắng lớn
                - Đòi hỏi kiên nhẫn và kỷ luật
                - Quan trọng: Đừng cắt lãi sớm
                """)
            elif ty_le_thang > 55 and ty_le_ln_lo < 1.0:
                st.warning("""
                ⚠️ **Hồ sơ mean-reversion có rủi ro**  
                - Thắng nhỏ thường xuyên, thua lớn đôi khi
                - Cảnh báo: Dễ bị tổn thương bởi tail event
                - **Hành động:** Áp dụng stop-loss nghiêm ngặt
                """)
        
        # Phân tích biến động
        with st.expander("📊 Phân Tích Biến Động & Ổn Định"):
            bien_dong_nam = tom_tat['Annual_Volatility'] * 100
            
            st.markdown(f"""
            **Biến Động Hàng Năm: {bien_dong_nam:.1f}%**
            
            **Diễn Giải Biến Động:**
            - Đo lường mức độ dao động lợi nhuận năm này qua năm khác
            - Biến động cao = lợi nhuận khó đoán hơn
            - Biến động của bạn: {bien_dong_nam:.1f}%
            - Biến động S&P 500 thường: ~20%
            """)
            
            if bien_dong_nam < 20:
                st.success(f"""
                ✅ **Chiến lược biến động thấp**  
                - Biến động {bien_dong_nam:.1f}% rất ổn định
                - Đường equity mượt mà
                - Phù hợp cho nhà đầu tư ngại rủi ro
                - **Cơ hội:** Có thể sử dụng đòn bẩy vừa phải (1.5-2x)
                """)
            elif bien_dong_nam < 35:
                st.info(f"""
                📊 **Biến động trung bình**  
                - {bien_dong_nam:.1f}% là điển hình cho chiến lược quant
                - Dự kiến một số dao động hàng tháng
                - Lợi nhuận điều chỉnh rủi ro (Sharpe {sharpe:.2f}) là then chốt
                - **Kích thước vị thế:** Phân bổ tiêu chuẩn OK
                """)
            else:
                st.warning(f"""
                ⚠️ **Biến động cao - Cần quản lý cẩn thận**  
                - Biến động {bien_dong_nam:.1f}% nghĩa là dao động lớn hàng tháng
                - Dao động ±{bien_dong_nam/12:.1f}% mỗi tháng
                - **Quản lý rủi ro cần thiết:**
                  - Giảm kích thước vị thế
                  - Áp dụng volatility targeting
                  - Sử dụng stop-loss rộng hơn (tránh whipsaw)
                """)
        
        st.markdown("---")
        
        # === PHẦN 3: BIỂU ĐỒ EQUITY ===
        st.markdown("### Biểu Đồ Equity Danh Mục")
        
        df_equity['Phan_Tram_LN'] = (df_equity['Cumulative_Return'] - 1) * 100
        
        fig = tao_bieu_do_chuyen_nghiep(df_equity, "Lợi Nhuận Tích Lũy", "Phan_Tram_LN")
        st.plotly_chart(fig, use_container_width=True)
        
        # Biểu đồ Drawdown
        st.markdown("### Sụt Giảm Theo Thời Gian")
        df_equity['Dinh'] = df_equity['Cumulative_Return'].cummax()
        df_equity['Phan_Tram_DD'] = ((df_equity['Cumulative_Return'] - df_equity['Dinh']) / df_equity['Dinh'] * 100)
        
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=df_equity.index,
            y=df_equity['Phan_Tram_DD'],
            fill='tozeroy',
            name='Sụt Giảm',
            line=dict(color='#c62828', width=2)
        ))
        
        fig_dd.update_layout(
            title="Sụt Giảm Danh Mục",
            xaxis_title="Ngày",
            yaxis_title="Sụt Giảm %",
            plot_bgcolor='white',
            font=dict(family='Inter'),
            height=300
        )
        
        st.plotly_chart(fig_dd, use_container_width=True)
        
        # === PHẦN 4: KHUYẾN NGHỊ HÀNH ĐỘNG ===
        st.markdown("### 💡 Khuyến Nghị Hành Động")
        
        khuyen_nghi = []
        
        # Dựa trên Sharpe
        if sharpe > 1.5:
            khuyen_nghi.append(("✅ TRIỂN KHAI", "Chiến lược sẵn sàng giao dịch thực với Sharpe cấp tổ chức"))
        elif sharpe > 1.0:
            khuyen_nghi.append(("⚠️ TỐI ƯU", "Hiệu suất tốt - cân nhắc giảm DD để đạt Grade A"))
        else:
            khuyen_nghi.append(("🔄 XEM XÉT", "Sharpe < 1.0 - xem lại chất lượng tín hiệu và cách kết hợp"))
        
        # Dựa trên DD
        if abs(max_dd) > 45:
            khuyen_nghi.append(("📉 GIẢM DD", f"Áp dụng stop-loss và volatility targeting (mục tiêu: -30%)"))
        
        # Dựa trên Win Rate & PF
        if profit_factor < 1.3:
            khuyen_nghi.append(("🎯 CẢI THIỆN LỢI THẾ", "Profit factor thấp - xem lại thời điểm vào/ra lệnh"))
        
        # Dựa trên biến động
        if bien_dong_nam > 40:
            khuyen_nghi.append(("📊 HẠ BIẾN ĐỘNG", "Biến động cao - giảm kích thước vị thế 30-50%"))
        
        for hanh_dong, mo_ta in khuyen_nghi:
            st.info(f"**{hanh_dong}:** {mo_ta}")
        
        st.markdown("---")
        
        # === PHẦN 5: BẢNG CHỈ SỐ CHI TIẾT ===
        st.markdown("### Bảng Chỉ Số Hiệu Suất Đầy Đủ")
        st.dataframe(du_lieu['tom_tat'], use_container_width=True, height=200)
    
    # TAB 3: TÍN HIỆU GIAO DỊCH
    with tabs[2]:
        st.markdown('<h2>Phân Tích Tín Hiệu Giao Dịch</h2>', unsafe_allow_html=True)
        
        if du_lieu['signals']:
            # Pass the full du_lieu dict which now has 'signals' key
            cluster_name = list(du_lieu['signals'].keys())[0] if du_lieu['signals'] else None
            if cluster_name:
                display_signal_analysis_tab(du_lieu, cluster_name)
            else:
                st.info("Không có dữ liệu tín hiệu cho kịch bản này")
        else:
            st.info("Không có dữ liệu tín hiệu cho kịch bản này")
    
    # TAB 4: TRỢ LÝ AI
    with tabs[3]:
        st.markdown('<h2>Trợ Lý AI Gemini</h2>', unsafe_allow_html=True)
        chat_tab(du_lieu)


if __name__ == "__main__":
    main()
