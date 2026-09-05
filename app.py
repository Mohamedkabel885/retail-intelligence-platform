import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import sqlite3
import hashlib

# ReportLab for PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ML Models & Metrics
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

try:
    from xgboost import XGBRegressor
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.data_processing import load_and_clean_data

# 1. Page Configuration
st.set_page_config(
    page_title="Enterprise Retail Intelligence Platform", 
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Clean, Static & Smooth Modern UI)
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f17;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #00f2fe !important;
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }

    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 14px 18px;
        border-radius: 12px;
    }

    .ai-summary-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%);
        border: 1px solid rgba(0, 212, 177, 0.3);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 25px;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161e2e;
        padding: 6px 10px;
        border-radius: 25px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 20px !important;
        color: #94a3b8;
        padding: 6px 16px;
        font-weight: 500;
        font-size: 13px;
        height: 36px;
        box-sizing: border-box;
        transition: none !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        background: rgba(255, 255, 255, 0.05);
    }

    .stTabs [aria-selected="true"] {
        background: #00d4b1 !important;
        color: #0b0f17 !important;
        font-weight: 600 !important;
        border-radius: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- 🗄️ DATABASE SETUP FOR REAL USERS & PASSWORDS ----------------
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(email, name, password):
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (email, name, password) VALUES (?, ?, ?)", (email, name, hash_password(password)))
        conn.commit()
        conn.close()
        return True, "تم إنشاء الحساب بنجاح!"
    except sqlite3.IntegrityError:
        return False, "البريد الإلكتروني مسجل مسبقاً!"

def verify_user(email, password):
    if email == "admin@enterprise.com" and password == "123456":
        return True, "مدير النظام"
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT name, password FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    
    if user and user[1] == hash_password(password):
        return True, user[0]
    return False, None

# ---------------- 🔐 AUTHENTICATION STATE CHECK ----------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 40px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); height: 100%;">
                <div style="background: rgba(0, 212, 177, 0.1); color: #00d4b1; padding: 6px 14px; border-radius: 20px; display: inline-block; font-size: 12px; font-weight: 600; margin-bottom: 20px;">
                    ✨ Enterprise Platform
                </div>
                <h1 style="color: white; font-size: 32px; font-weight: 800; margin-bottom: 15px;">
                    Start Your Retail Intelligence Journey Today
                </h1>
                <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin-bottom: 25px;">
                    Gain full access to real-time analytics, predictive AI sales forecasting, automated anomaly detection, and executive reporting tools.
                </p>
                <ul style="color: #cbd5e1; font-size: 13px; line-height: 2; list-style-type: none; padding-left: 0;">
                    <li>✅ Advanced Machine Learning Benchmarking</li>
                    <li>✅ Automated Threshold & Email Alerts</li>
                    <li>✅ Interactive What-If Scenario Simulators</li>
                    <li>✅ Instant Executive PDF Report Generation</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("""
            <div style="background: #0f172a; padding: 40px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.08);">
        """, unsafe_allow_html=True)
        
        auth_mode = st.radio("اختر العملية", ["Sign In", "Create Account"], horizontal=True, label_visibility="collapsed")
        
        if auth_mode == "Sign In":
            st.markdown("<h3 style='color: white; margin-bottom: 5px;'>Sign In to your account</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #94a3b8; font-size: 13px; margin-bottom: 25px;'>Enter your credentials to access the workspace</p>", unsafe_allow_html=True)
            
            if 'forgot_mode' not in st.session_state:
                st.session_state.forgot_mode = False

            if not st.session_state.forgot_mode:
                with st.form("login_form"):
                    email_input = st.text_input("Email address", placeholder="admin@enterprise.com")
                    password_input = st.text_input("Password", type="password", placeholder="••••••••")
                    st.caption("💡 **Demo Credentials:** admin@enterprise.com / 123456 (أو سجل حسابك الخاص)")
                    
                    submit_btn = st.form_submit_button("Sign In", use_container_width=True)
                    
                    if submit_btn:
                        success, user_name = verify_user(email_input, password_input)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user_name = user_name
                            st.success(f"أهلاً بك يا {user_name}! جاري تحميل لوحة التحكم...")
                            st.rerun()
                        else:
                            st.error("البريد الإلكتروني أو كلمة المرور غير صحيحة.")
                
                if st.button("Forgot Password?", use_container_width=True, type="tertiary"):
                    st.session_state.forgot_mode = True
                    st.rerun()
            
            else:
                st.markdown("<h4 style='color: #00d4b1;'>Reset Your Password</h4>", unsafe_allow_html=True)
                with st.form("forgot_form"):
                    reset_email = st.text_input("Enter your registered Email", placeholder="yourname@company.com")
                    new_password = st.text_input("Enter New Password", type="password", placeholder="••••••••")
                    
                    reset_btn = st.form_submit_button("Update Password", use_container_width=True)
                    back_btn = st.form_submit_button("Back to Sign In", use_container_width=True)
                    
                    if reset_btn:
                        if not reset_email or not new_password:
                            st.warning("يرجى إدخال البريد وكلمة المرور الجديدة.")
                        else:
                            conn = sqlite3.connect('users.db')
                            c = conn.cursor()
                            c.execute("SELECT name FROM users WHERE email = ?", (reset_email,))
                            user_exists = c.fetchone()
                            
                            if user_exists:
                                c.execute("UPDATE users SET password = ? WHERE email = ?", (hash_password(new_password), reset_email))
                                conn.commit()
                                conn.close()
                                st.success("تم تحديث كلمة المرور بنجاح! يمكنك تسجيل الدخول الآن.")
                            else:
                                conn.close()
                                st.error("البريد الإلكتروني غير مسجل لدينا.")
                                
                    if back_btn:
                        st.session_state.forgot_mode = False
                        st.rerun()
        else:
            st.markdown("<h3 style='color: white; margin-bottom: 5px;'>Create your account</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #94a3b8; font-size: 13px; margin-bottom: 25px;'>Fill in your professional details to get started</p>", unsafe_allow_html=True)
            
            with st.form("signup_form"):
                name_input = st.text_input("Full name", placeholder="John Doe")
                email_input = st.text_input("Email address", placeholder="yourname@company.com")
                password_input = st.text_input("Password", type="password", placeholder="••••••••")
                
                signup_btn = st.form_submit_button("Create Account", use_container_width=True)
                
                if signup_btn:
                    if not name_input or not email_input or not password_input:
                        st.warning("يرجى ملء جميع الحقول المطلوبة.")
                    else:
                        success, msg = add_user(email_input, name_input, password_input)
                        if success:
                            st.success(f"{msg} قم بالتبديل إلى Sign In وتسجيل الدخول الآن.")
                        else:
                            st.error(msg)
                            
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.stop()

# ---------------- 🚀 MAIN APP (AFTER SUCCESSFUL LOGIN) ----------------

def generate_pdf_report(tot_sales, avg_sales, active_count, target_pct, ai_summary_text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#0f172a'), spaceAfter=10)
    subtitle_style = ParagraphStyle('SubTitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#64748b'), spaceAfter=20)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#00d4b1'), spaceAfter=10)
    text_style = ParagraphStyle('Text', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#334155'), leading=14)

    story.append(Paragraph("💎 Enterprise Retail Executive Brief", title_style))
    story.append(Paragraph(f"Generated for: {st.session_state.get('user_name', 'Client')} • Retail Intelligence AI Platform", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=15))

    data = [
        ["Total Sales", "Avg Store Revenue", "Active Stores", "Target Progress"],
        [f"${tot_sales:,.0f}", f"${avg_sales:,.0f}", f"{active_count}", f"{target_pct}%"]
    ]
    t = Table(data, colWidths=[130, 130, 100, 130])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0,1), (-1,1), colors.HexColor('#0f172a')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 11),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    story.append(Paragraph("📌 Executive Insights & AI Analysis", heading_style))
    for line in ai_summary_text.split('\n'):
        if line.strip():
            story.append(Paragraph(line.strip(), text_style))
            story.append(Spacer(1, 4))

    doc.build(story)
    buffer.seek(0)
    return buffer

def send_email_alert(receiver_email, subject, body_text, smtp_sender, smtp_password):
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_sender
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_sender, smtp_password)
        server.send_message(msg)
        server.quit()
        return True, "تم إرسال التنبيه بنجاح عبر البريد الإلكتروني!"
    except Exception as e:
        return False, f"فشل الإرسال: {str(e)}"

@st.cache_data
def get_data():
    return load_and_clean_data()

try:
    df = get_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# ---------------- ⚡ INTERACTIVE UI CONTROLS ----------------
st.sidebar.markdown(f"👤 **Welcome, {st.session_state.get('user_name', 'Client')}!**")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Interactive Controls")

all_stores = sorted(df['store_id'].unique())
min_date = df['date'].min().date()
max_date = df['date'].max().date()

if 'selected_stores_key' not in st.session_state:
    st.session_state.selected_stores_key = all_stores[:3]

st.sidebar.caption("⚡ Quick Preset Selection")
preset_col1, preset_col2 = st.sidebar.columns(2)

if preset_col1.button("Select All Stores", use_container_width=True):
    st.session_state.selected_stores_key = all_stores
    st.rerun()

if preset_col2.button("Top 3 Stores", use_container_width=True):
    top_3 = df.groupby('store_id')['weekly_sales'].sum().nlargest(3).index.tolist()
    st.session_state.selected_stores_key = top_3
    st.rerun()

selected_stores = st.sidebar.multiselect(
    "Select Store ID", 
    options=all_stores, 
    key="selected_stores_key"
)

date_range = st.sidebar.date_input(
    "Select Date Range", 
    [min_date, max_date]
)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

filtered_df = df[(df['store_id'].isin(selected_stores)) & 
                (df['date'] >= pd.to_datetime(date_range[0])) & 
                (df['date'] <= pd.to_datetime(date_range[1]))]

st.markdown("""
    <div style='padding: 5px 0px 15px 0px;'>
        <h2 style='font-weight: 700; color: #ffffff; margin: 0;'>
            💎 Enterprise Retail Intelligence Engine
        </h2>
        <p style='color: #64748b; font-size: 13px; margin-top: 4px;'>
            Real-Time Analytics • Predictive AI Forecasting • Executive Reporting
        </p>
    </div>
""", unsafe_allow_html=True)

tot_sales = filtered_df['weekly_sales'].sum()
avg_sales = filtered_df.groupby('store_id')['weekly_sales'].sum().mean() if not filtered_df.empty else 0
active_count = filtered_df['store_id'].nunique()
holiday_sales = filtered_df[filtered_df['is_holiday']==True]['weekly_sales'].mean()
tot_markdowns = filtered_df['total_markdown'].sum()

SALES_TARGET = 50000000
target_pct = min(100, int((tot_sales / SALES_TARGET) * 100)) if SALES_TARGET > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Sales", f"${tot_sales:,.0f}")
col2.metric("Avg Store Revenue", f"${avg_sales:,.0f}")
col3.metric("Active Stores", f"{active_count}")
col4.metric("Avg Holiday Sales", f"${0 if np.isnan(holiday_sales) else holiday_sales:,.0f}")
col5.metric("Total Markdowns", f"${tot_markdowns:,.0f}")

st.caption(f"🎯 **Target Performance Progress:** {target_pct}% achieved of goal (${SALES_TARGET:,.0f})")
st.progress(target_pct / 100)
st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Executive Dashboard", 
    "🔔 Smart Alert Center",
    "🌐 Economic & Markdowns", 
    "🔮 ML Forecast & Simulator", 
    "🧠 Advanced ML Algorithms",
    "🚨 Anomaly Detection",
    "🏬 Store Benchmarking",
    "📑 Export Data"
])

with tab1:
    top_store = filtered_df.groupby('store_id')['weekly_sales'].sum().idxmax() if not filtered_df.empty else "N/A"
    ai_summary_text = f"""
    • **إجمالي الإيرادات:** تم تحقيق إيرادات إجمالية بقيمة **${tot_sales:,.0f}** من أصل الهدف الإستراتيجي (${SALES_TARGET:,.0f}) بنسبة إنجاز بلغت **{target_pct}%**.
    • **أعلى الفروع أداءً:** يتصدر **الفرع رقم {top_store}** قائمة الفروع الأكثر إيراداً ضمن النطاق المالي المختار.
    • **تأثير العروض:** بلغت الخصومات والتخفيضات الكلية **${tot_markdowns:,.0f}** محققة أثراً إيجابياً متوازناً على حجم المبيعات الإجمالي.
    • **التوصية:** يوصى بمتابعة معدلات التضخم والتركيز على دعم الفروع ذات النمو المتوسط لتعظيم الربحية الكلية.
    """

    st.markdown(f"""
        <div class="ai-summary-card">
            <h4 style="color: #00d4b1; margin-top: 0;">🤖 AI Executive Summary & Narrative Insights</h4>
            <div style="color: #e2e8f0; font-size: 14px; line-height: 1.6;">
                {ai_summary_text.replace(chr(10), '<br>')}
            </div>
        </div>
    """, unsafe_allow_html=True)

    pdf_file = generate_pdf_report(tot_sales, avg_sales, active_count, target_pct, ai_summary_text)
    st.download_button(
        label="📄 Download Executive PDF Report",
        data=pdf_file,
        file_name="executive_retail_report.pdf",
        mime="application/pdf",
        use_container_width=False
    )
    st.markdown("<br>", unsafe_allow_html=True)

    r1_col1, r1_col2 = st.columns([2, 1])
    with r1_col1:
        st.markdown("#### 📈 Revenue Performance Trend")
        trend_df = filtered_df.groupby('date')['weekly_sales'].sum().reset_index()
        fig_trend = px.line(trend_df, x='date', y='weekly_sales', template="plotly_dark", color_discrete_sequence=['#00d4b1'])
        fig_trend.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_trend, use_container_width=True)

    with r1_col2:
        st.markdown("#### 🏬 Store Type Contribution")
        type_df = filtered_df.groupby('type')['weekly_sales'].sum().reset_index()
        fig_pie = px.pie(type_df, values='weekly_sales', names='type', hole=0.5, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Bold)
        fig_pie.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)

with tab2:
    st.markdown("### 🔔 Automated Threshold & Email Alerting System")
    c_conf1, c_conf2 = st.columns([1, 1])
    
    with c_conf1:
        st.markdown("##### ⚙️ 1. Threshold Configuration")
        sales_threshold = st.number_input("Minimum Acceptable Weekly Sales ($)", min_value=1000, max_value=1000000, value=15000, step=1000)
        low_sales_df = filtered_df[filtered_df['weekly_sales'] < sales_threshold]
        flagged_count = low_sales_df['store_id'].nunique()

        if flagged_count > 0:
            st.error(f"⚠️ تم اكتشاف **{flagged_count}** فرع انخفضت مبيعاتهم عن الحد المسموح (${sales_threshold:,.0f})")
            summary_low = low_sales_df.groupby('store_id').agg(
                Lowest_Sales=('weekly_sales', 'min'),
                Low_Weeks_Count=('weekly_sales', 'count')
            ).reset_index()
            st.dataframe(summary_low.style.format({'Lowest_Sales': '${:,.0f}'}), use_container_width=True)
        else:
            st.success("جميع الفروع المحددة تحقق أداءً أعلى من الحد الأدنى المقبول. ✅")

    with c_conf2:
        st.markdown("##### 📧 2. Send Email Notification")
        user_email = st.text_input("Receiver Email Address", placeholder="manager@company.com")
        with st.expander("🔑 SMTP Mail Server Settings (Optional)"):
            smtp_sender = st.text_input("Sender Gmail", placeholder="your_app_email@gmail.com")
            smtp_pass = st.text_input("App Password", type="password")

        if st.button("🚀 Trigger Email Alert Now", use_container_width=True):
            if not user_email:
                st.warning("يرجى إدخال البريد الإلكتروني للمستقبل أولاً.")
            else:
                if smtp_sender and smtp_pass:
                    subject = f"⚠️ Sales Alert: {flagged_count} Stores Below Threshold"
                    email_body = f"<h2>Alert</h2><p>Affected stores: {flagged_count}</p>"
                    success, msg = send_email_alert(user_email, subject, email_body, smtp_sender, smtp_pass)
                    if success: st.success(msg)
                    else: st.error(msg)
                else:
                    st.success(f"✅ (وضع المحاكاة) تم إرسال التنبيه بنجاح إلى: {user_email}")

with tab3:
    st.markdown("### 🌐 Macroeconomic Drivers & Promotional Impact")
    e_col1, e_col2 = st.columns(2)
    with e_col1:
        st.markdown("##### 💵 CPI (Inflation) vs Weekly Sales")
        fig_cpi = px.scatter(filtered_df.sample(min(800, len(filtered_df))), x='cpi', y='weekly_sales', color='type', template="plotly_dark", opacity=0.75)
        fig_cpi.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_cpi, use_container_width=True)

    with e_col2:
        st.markdown("##### 📉 Unemployment Rate vs Sales")
        fig_unemp = px.scatter(filtered_df.sample(min(800, len(filtered_df))), x='unemployment', y='weekly_sales', color='type', template="plotly_dark", opacity=0.75)
        fig_unemp.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_unemp, use_container_width=True)

with tab4:
    st.markdown("### 🤖 AI Sales Forecasting & What-If Simulator")
    ml_col1, ml_col2 = st.columns([1, 2])
    with ml_col1:
        markdown_lift = st.slider("Simulate Promotional Increase (%)", 0, 100, 15)
        cpi_shift = st.slider("Simulate CPI Inflation Adjustment (%)", -10, 10, 0)
        run_btn = st.button("🚀 Train & Run Forecast Model", use_container_width=True)

    with ml_col2:
        if run_btn:
            with st.spinner("Running Prediction Pipeline..."):
                ml_df = df.groupby(['date', 'year', 'month', 'week_of_year'])[['weekly_sales', 'cpi', 'total_markdown']].sum().reset_index()
                ml_df['lag_1'] = ml_df['weekly_sales'].shift(1)
                ml_df.dropna(inplace=True)

                X = ml_df[['year', 'month', 'week_of_year', 'cpi', 'total_markdown', 'lag_1']]
                y = ml_df['weekly_sales']

                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(X, y)

                latest = X.iloc[-1:].copy()
                base_pred = model.predict(latest)[0]

                simulated = latest.copy()
                simulated['total_markdown'] *= (1 + markdown_lift / 100)
                simulated['cpi'] *= (1 + cpi_shift / 100)
                sim_pred = model.predict(simulated)[0]

                m_col1, m_col2 = st.columns(2)
                m_col1.metric("Baseline Sales Estimate", f"${base_pred:,.2f}")
                diff = sim_pred - base_pred
                m_col2.metric("Simulated Scenario Revenue", f"${sim_pred:,.2f}", delta=f"${diff:,.2f}")

with tab5:
    st.markdown("### 🧠 Multi-Algorithm Benchmarking & Feature Importance")
    algo_col1, algo_col2 = st.columns([1, 2])
    model_options = ["Random Forest Regressor", "Gradient Boosting Regressor", "Linear Regression"]
    if HAS_XGBOOST: model_options.insert(2, "XGBoost Regressor")

    with algo_col1:
        selected_model_name = st.selectbox("Choose Algorithm", model_options, key="algo_select")
        test_size = st.slider("Test Set Split Ratio (%)", 10, 40, 20, key="algo_test_size")
        eval_btn = st.button("⚡ Evaluate Algorithm Performance", use_container_width=True, key="algo_eval_btn")

    with algo_col2:
        if eval_btn or 'ml_eval_done' in st.session_state:
            st.session_state['ml_eval_done'] = True
            
            with st.spinner("Training model & generating visualizations..."):
                ml_df = df.groupby(['date', 'year', 'month', 'week_of_year'])[['weekly_sales', 'cpi', 'unemployment', 'fuel_price', 'total_markdown']].sum().reset_index()
                ml_df['lag_1'] = ml_df['weekly_sales'].shift(1)
                ml_df['lag_2'] = ml_df['weekly_sales'].shift(2)
                ml_df.dropna(inplace=True)

                feature_cols = ['year', 'month', 'week_of_year', 'cpi', 'unemployment', 'fuel_price', 'total_markdown', 'lag_1', 'lag_2']
                X = ml_df[feature_cols]
                y = ml_df['weekly_sales']
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size/100, random_state=42)

                if selected_model_name == "Random Forest Regressor": model = RandomForestRegressor(n_estimators=100, random_state=42)
                elif selected_model_name == "Gradient Boosting Regressor": model = GradientBoostingRegressor(n_estimators=100, random_state=42)
                elif HAS_XGBOOST and selected_model_name == "XGBoost Regressor": model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
                else: model = LinearRegression()

                model.fit(X_train, y_train)
                predictions = model.predict(X_test)
                
                mae = mean_absolute_error(y_test, predictions)
                rmse = np.sqrt(mean_squared_error(y_test, predictions))
                r2 = r2_score(y_test, predictions)
                r2_display = 0.0 if (np.isnan(r2) or np.isinf(r2)) else max(0.0, r2 * 100)

                m1, m2, m3 = st.columns(3)
                m1.metric("MAE", f"${mae:,.0f}")
                m2.metric("RMSE", f"${rmse:,.0f}")
                m3.metric("R² Score", f"{r2_display:.2f}%")
                
                st.markdown("<br>", unsafe_allow_html=True)

                res_df = pd.DataFrame({'Actual': y_test, 'Predicted': predictions}, index=y_test.index).sort_index()
                fig_res = px.line(res_df, template="plotly_dark", color_discrete_map={'Actual': '#00d4b1', 'Predicted': '#3b82f6'}, title=f"<b>{selected_model_name}: Actual vs Predicted Sales</b>")
                fig_res.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_res, use_container_width=True)

                if hasattr(model, 'feature_importances_'):
                    imp_df = pd.DataFrame({'Feature': feature_cols, 'Importance': model.feature_importances_}).sort_values('Importance', ascending=True)
                    fig_imp = px.bar(imp_df, x='Importance', y='Feature', orientation='h', template="plotly_dark", color='Importance', color_continuous_scale='Tealgrn', title="<b>Feature Importance Ranking</b>")
                    fig_imp.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_imp, use_container_width=True)

with tab6:
    st.markdown("### 🚨 Automated Anomaly Detection System (Isolation Forest)")
    contamination = st.slider("Anomaly Sensitivity Factor (%)", 1, 15, 5) / 100.0
    anomaly_df = filtered_df.groupby(['date', 'store_id'])['weekly_sales'].sum().reset_index()
    if len(anomaly_df) >= 3:
        iso = IsolationForest(contamination=contamination, random_state=42)
        anomaly_df['anomaly'] = iso.fit_predict(anomaly_df[['weekly_sales']])
        anomaly_df['Status'] = anomaly_df['anomaly'].map({1: 'Normal', -1: 'Anomaly Detected'})
        fig_anom = px.scatter(anomaly_df, x='date', y='weekly_sales', color='Status', color_discrete_map={'Normal': '#00d4b1', 'Anomaly Detected': '#ff4b4b'}, hover_data=['store_id'], template="plotly_dark")
        st.plotly_chart(fig_anom, use_container_width=True)

with tab7:
    st.markdown("### 🏬 Cross-Store Benchmarking & K-Means Clustering Matrix")
    store_summary = df.groupby('store_id').agg({'weekly_sales': 'sum', 'total_markdown': 'mean', 'cpi': 'mean'}).reset_index()
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(store_summary[['weekly_sales', 'total_markdown', 'cpi']])
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    store_summary['Cluster'] = kmeans.fit_predict(scaled_data)
    store_summary['Cluster'] = store_summary['Cluster'].apply(lambda x: f"Cluster {x+1}")
    fig_cluster = px.scatter(store_summary, x='total_markdown', y='weekly_sales', size='weekly_sales', color='Cluster', hover_name='store_id', text='store_id', template="plotly_dark")
    st.plotly_chart(fig_cluster, use_container_width=True)

with tab8:
    st.markdown("### 📑 Enterprise Dataset Explorer & Downloads")
    st.dataframe(filtered_df.head(150), use_container_width=True)
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Export Filtered Executive Data (CSV)", data=csv_data, file_name="executive_retail_report.csv", mime="text/csv", use_container_width=True)