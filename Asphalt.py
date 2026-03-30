import streamlit as st
import numpy as np
from scipy.optimize import fsolve

# --- 1. ฟังก์ชันคำนวณหา SN จากสมการ AASHTO 1993 ---
def aashto_sn_function(SN, ZR, So, W18, delta_PSI, MR):
    if SN < 0: return 999  # ป้องกันค่าติดลบ
    term1 = ZR * So
    term2 = 9.36 * np.log10(SN + 1) - 0.20
    term3 = np.log10(delta_PSI / (4.2 - 1.5)) / (0.40 + (1094 / (SN + 1)**5.19))
    term4 = 2.32 * np.log10(MR) - 8.07
    
    # f(SN) = 0
    return term1 + term2 + term3 + term4 - np.log10(W18)

def calculate_sn(ZR, So, W18, delta_PSI, MR):
    # ใช้ fsolve ในการหาค่า SN ที่ทำให้สมการเป็น 0
    sn_initial_guess = 3.0
    sn_solved = fsolve(aashto_sn_function, sn_initial_guess, args=(ZR, So, W18, delta_PSI, MR))
    return max(0, sn_solved[0])

# --- 2. การตั้งค่าหน้าจอ Streamlit ---
st.set_page_config(page_title="AASHTO 1993 Pavement Design", layout="wide")
st.title("🛣️ Flexible Pavement Design (AASHTO 1993)")
st.markdown("---")

# --- 3. Sidebar: ข้อมูลพื้นฐาน (Design Parameters) ---
st.sidebar.header("1. Design Parameters")
reliability = st.sidebar.selectbox("Reliability (R, %)", [80, 85, 90, 95, 98, 99], index=3)
# แปลง R เป็น ZR
r_to_zr = {80: -0.841, 85: -1.037, 90: -1.282, 95: -1.645, 98: -2.054, 99: -2.327}
ZR = r_to_zr[reliability]

So = st.sidebar.number_input("Standard Deviation (So)", value=0.45, step=0.01)
pi = st.sidebar.number_input("Initial Serviceability (pi)", value=4.2, step=0.1)
pt = st.sidebar.number_input("Terminal Serviceability (pt)", value=2.5, step=0.1)
delta_PSI = pi - pt

# --- 4. Main Page: แบ่งเป็น Columns ---
col1, col2 = st.columns(2)

with col1:
    st.header("2. Traffic & Subgrade")
    w18 = st.number_input("Design ESALs (W18)", value=1000000, step=100000, format="%d")
    cbr_subgrade = st.number_input("Subgrade CBR (%)", value=5.0, step=0.5)
    mr_subgrade = 1500 * cbr_subgrade  # สูตรพื้นฐาน MR = 1500 * CBR
    st.info(f"Calculated Subgrade MR: {mr_subgrade:,.0f} psi")

    st.header("3. Layer Coefficients & Drainage")
    a1 = st.number_input("Surface Coefficient (a1) - e.g., Asphalt", value=0.44, step=0.01)
    
    c2 = st.columns(2)
    a2 = c2[0].number_input("Base Coefficient (a2)", value=0.14, step=0.01)
    m2 = c2[1].number_input("Base Drainage (m2)", value=1.0, step=0.1)
    
    c3 = st.columns(2)
    a3 = c3[0].number_input("Subbase Coefficient (a3)", value=0.11, step=0.01)
    m3 = c3[1].number_input("Subbase Drainage (m3)", value=1.0, step=0.1)

with col2:
    st.header("4. Results & Thickness Selection")
    
    # คำนวณ SN required
    sn_req = calculate_sn(ZR, So, w18, delta_PSI, mr_subgrade)
    st.success(f"### Required Structural Number (SN_req): {sn_req:.3f}")
    
    st.markdown("---")
    st.subheader("Input Design Thickness (inches)")
    d1 = st.number_input("Surface Thickness (D1)", value=3.0, step=0.5)
    d2 = st.number_input("Base Thickness (D2)", value=6.0, step=1.0)
    d3 = st.number_input("Subbase Thickness (D3)", value=8.0, step=1.0)
    
    # คำนวณ SN Provided
    sn_provided = (a1 * d1) + (a2 * d2 * m2) + (a3 * d3 * m3)
    
    # ตรวจสอบความหนาขั้นต่ำ (Minimum Thickness) ตาม AASHTO
    def check_min_thickness(w18, d1, d2):
        min_d1, min_d2 = 0, 0
        if w18 < 50000: min_d1, min_d2 = 1.0, 4.0
        elif w18 < 150000: min_d1, min_d2 = 2.0, 4.0
        elif w18 < 500000: min_d1, min_d2 = 2.5, 4.0
        elif w18 < 2000000: min_d1, min_d2 = 3.0, 6.0
        elif w18 < 7000000: min_d1, min_d2 = 3.5, 6.0
        else: min_d1, min_d2 = 4.0, 6.0
        return min_d1, min_d2

    min_d1, min_d2 = check_min_thickness(w18, d1, d2)

    # --- ส่วนแสดงผลลัพธ์สุดท้าย ---
    st.markdown("---")
    st.metric("Total SN Provided", f"{sn_provided:.3f}", delta=f"{sn_provided - sn_req:.3f}")

    if sn_provided >= sn_req:
        st.balloons()
        st.success("✅ โครงสร้างผ่านเกณฑ์ (Adequate)")
    else:
        st.error("❌ โครงสร้างไม่เพียงพอ (Inadequate) - กรุณาเพิ่มความหนา")

    # ตรวจสอบเกณฑ์ขั้นต่ำ
    if d1 < min_d1 or d2 < min_d2:
        st.warning(f"⚠️ คำเตือน: ความหนาต่ำกว่าเกณฑ์ขั้นต่ำของ AASHTO (D1 min: {min_d1}\", D2 min: {min_d2}\")")

# --- 5. ตารางสรุปวัสดุ (Reference Table) ---
with st.expander("ดูตารางอ้างอิงค่า Coefficient (ai) มาตรฐาน"):
    st.write("""
    - **Asphalt Concrete Surface**: 0.44
    - **Crushed Stone Base (CBR 80%)**: 0.14
    - **Cement Treated Base (7-day 650 psi)**: 0.20
    - **Sandy Gravel Subbase (CBR 30%)**: 0.11
    - **Soil Aggregate Subbase (CBR 20%)**: 0.10
    """)
