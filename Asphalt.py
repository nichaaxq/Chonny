import streamlit as st
import numpy as np
from scipy.optimize import fsolve

# --- 1. ฟังก์ชันคำนวณหลัก (Mathematical Engines) ---

def aashto_flexible(SN, ZR, So, W18, delta_PSI, MR):
    """สมการหาค่า SN สำหรับ Flexible Pavement"""
    if SN <= 0: return 1e6
    term1 = ZR * So
    term2 = 9.36 * np.log10(SN + 1) - 0.20
    term3 = np.log10(delta_PSI / (4.2 - 1.5)) / (0.40 + (1094 / (SN + 1)**5.19))
    term4 = 2.32 * np.log10(MR) - 8.07
    return term1 + term2 + term3 + term4 - np.log10(W18)

def aashto_rigid(D, ZR, So, W18, delta_PSI, Sc, Cd, J, Ec, k):
    """สมการหาค่าความหนา D สำหรับ Rigid Pavement"""
    if D <= 0: return 1e6
    term1 = ZR * So
    term2 = 7.35 * np.log10(D + 1) - 0.06
    term3 = np.log10(delta_PSI / (4.5 - 1.5)) / (1 + (1.624e7 / (D + 1)**8.46))
    term4 = (4.22 - 0.32 * 2.5) * np.log10((Sc * Cd * (D**0.75 - 1.132)) / (215.63 * J * (D**0.75 - (18.42 / (Ec / k)**0.25))))
    return term1 + term2 + term3 + term4 - np.log10(W18)

# --- 2. การตั้งค่าหน้าจอ (UI Setup) ---
st.set_page_config(page_title="Pavement Design Expert", layout="wide")
st.title("🛣️ Professional Pavement Design Tool (AASHTO 1993)")
st.markdown("โปรแกรมคำนวณความหนาผิวทางตามมาตรฐาน AASHTO ครบวงจร")

# --- 3. Sidebar: เลือกประเภทและค่าคงที่พื้นฐาน ---
st.sidebar.header("Step 1: Project Type")
pavement_type = st.sidebar.radio("ประเภทผิวทาง:", ["Flexible (ลาดยาง AC)", "Rigid (คอนกรีต JPCP)"])

st.sidebar.header("Step 2: Reliability & Serviceability")
rel_val = st.sidebar.selectbox("Reliability (R, %):", [80, 85, 90, 95, 98, 99], index=3)
r_to_zr = {80: -0.841, 85: -1.037, 90: -1.282, 95: -1.645, 98: -2.054, 99: -2.327}
ZR = r_to_zr[rel_val]
So = st.sidebar.number_input("Standard Deviation (So):", value=0.45 if "Flexible" in pavement_type else 0.35)
pi = st.sidebar.number_input("Initial Serviceability (pi):", value=4.2 if "Flexible" in pavement_type else 4.5)
pt = st.sidebar.number_input("Terminal Serviceability (pt):", value=2.5)
delta_PSI = pi - pt

# --- 4. Main Page: Traffic Analysis (Step 3) ---
st.header("Step 3: Traffic Analysis (ESALs)")
traffic_option = st.radio("วิธีการระบุปริมาณจราจร:", ["ใส่ค่า ESALs โดยตรง", "คำนวณจากประเภทรถ (Truck Factor)"])

if traffic_option == "คำนวณจากประเภทรถ (Truck Factor)":
    t_col1, t_col2, t_col3 = st.columns(3)
    with t_col1:
        v6 = st.number_input("รถบรรทุก 6 ล้อ (คัน/วัน)", value=200)
        v10 = st.number_input("รถบรรทุก 10 ล้อ (คัน/วัน)", value=100)
        v_tr = st.number_input("รถพ่วง/เทรลเลอร์ (คัน/วัน)", value=50)
    with t_col2:
        growth = st.number_input("Growth Rate (%)", value=3.0) / 100
        period = st.number_input("อายุการใช้งาน (ปี)", value=15)
        lane_dist = st.slider("Lane Distribution (DL)", 0.1, 1.0, 0.5)
    with t_col3:
        # Truck Factors (Default Values)
        tf6 = st.number_input("Truck Factor (6-Wheel)", value=0.29)
        tf10 = st.number_input("Truck Factor (10-Wheel)", value=1.28)
        tf_tr = st.number_input("Truck Factor (Trailer)", value=2.50)
    
    gf = ((1 + growth)**period - 1) / growth
    w18 = ((v6*tf6) + (v10*tf10) + (v_tr*tf_tr)) * 365 * gf * lane_dist
    st.info(f"💡 ปริมาณจราจรสะสมที่คำนวณได้: **{w18:,.0f} ESALs**")
else:
    w18 = st.number_input("ระบุ Design ESALs (W18) โดยตรง:", value=1000000)

st.markdown("---")

# --- 5. การคำนวณตาม
