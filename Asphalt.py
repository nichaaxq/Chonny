import streamlit as st
import numpy as np
from scipy.optimize import fsolve

# --- 1. Mathematical Functions ---
def aashto_flexible(SN, ZR, So, W18, delta_PSI, MR):
    if SN <= 0: return 1e6
    return ZR * So + 9.36 * np.log10(SN + 1) - 0.20 + (np.log10(delta_PSI / 2.7) / (0.40 + (1094 / (SN + 1)**5.19))) + 2.32 * np.log10(MR) - 8.07 - np.log10(W18)

def aashto_rigid(D, ZR, So, W18, delta_PSI, Sc, Cd, J, Ec, k):
    if D <= 0: return 1e6
    term4 = (4.22 - 0.32 * 2.5) * np.log10((Sc * Cd * (D**0.75 - 1.132)) / (215.63 * J * (D**0.75 - (18.42 / (Ec / k)**0.25))))
    return ZR * So + 7.35 * np.log10(D + 1) - 0.06 + (np.log10(delta_PSI / 3.0) / (1 + (1.624e7 / (D + 1)**8.46))) + term4 - np.log10(W18)

def calc_truck_factor(single_ton, single_count, tandem_ton, tandem_count, tridem_ton, tridem_count):
    # Conversion: 1 Tonne = 2.20462 kips
    s_lef = ( (single_ton * 2.20462) / 18 )**4 * single_count
    t_lef = ( (tandem_ton * 2.20462) / 33.2 )**4 * tandem_count
    tr_lef = ( (tridem_ton * 2.20462) / 45.4 )**4 * tridem_count
    return s_lef + t_lef + tr_lef

# --- 2. UI Setup ---
st.set_page_config(page_title="Pavement Design Detail", layout="wide")
st.title("🛣️ AASHTO 1993: Detailed Vehicle & Pavement Design")

# --- 3. Step 1: Detailed Traffic Analysis ---
st.header("Step 1: Detailed Traffic & Truck Factor Analysis")

with st.expander("🚚 กำหนดค่า Truck Factor (TF) สำหรับรถแต่ละประเภท (หน่วย: ตัน)", expanded=True):
    st.write("ระบุน้ำหนักลงเพลาเฉลี่ยเพื่อหา TF รายประเภทรถ")
    
    # สร้างคอลัมน์สำหรับตั้งค่า TF พื้นฐาน
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Buses (MB, HB)")
        tf_mb = st.number_input("Truck Factor - MB (Medium Bus)", value=0.20, format="%.3f")
        tf_hb = st.number_input("Truck Factor - HB (Heavy Bus)", value=0.40, format="%.3f")
    with c2:
        st.subheader("Trucks (MT, HT)")
        tf_mt = st.number_input("Truck Factor - MT (Medium Truck)", value=0.30, format="%.3f")
        tf_ht = st.number_input("Truck Factor - HT (Heavy Truck)", value=1.30, format="%.3f")
    with c3:
        st.subheader("Heavy (TR, STR)")
        tf_tr = st.number_input("Truck Factor - TR (Full-Trailer)", value=2.50, format="%.3f")
        tf_str = st.number_input("Truck Factor - STR (Semi-Trailer)", value=2.10, format="%.3f")

st.subheader("🔢 ปริมาณรถบรรทุกรายวัน (AADT)")
v_col1, v_col2, v_col3 = st.columns(3)
with v_col1:
    count_mb = st.number_input("AADT: MB (Medium Bus)", value=50)
    count_hb = st.number_input("AADT: HB (Heavy Bus)", value=30)
with v_col2:
    count_mt = st.number_input("AADT: MT (Medium Truck)", value=100)
    count_ht = st.number_input("AADT: HT (Heavy Truck)", value=150)
with v_col3:
    count_tr = st.number_input("AADT: TR (Trailer)", value=40)
    count_str = st.number_input("AADT: STR (Semi-Trailer)", value=60)

# --- Calculation of total ESALs per day ---
total_daily_esal = (count_mb * tf_mb) + (count_hb * tf_hb) + (count_mt * tf_mt) + \
                   (count_ht * tf_ht) + (count_tr * tf_tr) + (count_str * tf_str)

# --- Traffic Factors (Growth, Lane) ---
st.markdown("---")
g_col1, g_col2 = st.columns(2)
with g_col1:
    growth = st.number_input("Growth Rate (%)", value=3.0) / 100
    period = st.number_input("Design Life (Years)", value=20)
    gf = ((1 + growth)**period - 1) / growth
with g_col2:
    lane_dist = st.slider("Lane Distribution Factor (DL)", 0.1, 1.0, 0.5)
    w18 = total_daily_esal * 365 * gf * lane_dist

st.success(f"📈 **Total Design ESALs (W18): {w18:,.0f}**")

# --- 4. Sidebar: Design Parameters ---
st.sidebar.header("Design Parameters")
p_type = st.sidebar.selectbox("Pavement Type", ["Flexible (AC)", "Rigid (Concrete)"])
rel = st.sidebar.selectbox("Reliability (R%)", [80, 85, 90, 95, 98, 99], index=3)
r_to_zr = {80: -0.841, 85: -1.037, 90: -1.282, 95: -1.645, 98: -2.054, 99: -2.327}
ZR = r_to_zr[rel]
So = st.sidebar.slider("Standard Deviation (So)", 0.3, 0.5, 0.45 if "Flexible" in p_type else 0.35)
pi = st.sidebar.number_input("Initial Serviceability (pi)", value=4.2 if "Flexible" in p_type else 4.5)
pt = st.sidebar.number_input("Terminal Serviceability (pt)", value=2.5)

# --- 5. Step 2: Structural Design ---
st.header(f"Step 2: ออกแบบความหนา ({p_type})")
d_col1, d_col2 = st.columns(2)

if "Flexible" in p_type:
    with d_col1:
        cbr = st.number_input("Subgrade CBR (%)", value=5.0)
        mr = 1500 * cbr
        a1, a
