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

# --- 2. UI Setup ---
st.set_page_config(page_title="Pavement Design (Metric Unit)", layout="wide")
st.title("🛣️ AASHTO 1993: Axle Load (Tonnes) & Pavement Design")

# --- 3. Step 1: Truck Factor Calculator (Units: Tonnes) ---
st.header("Step 1: คำนวณ Truck Factor จากน้ำหนักลงเพลา (หน่วย: ตัน)")
with st.expander("เปิดส่วนคำนวณน้ำหนักลงเพลา", expanded=True):
    st.write("ป้อนน้ำหนักลงเพลาเป็น 'ตัน' ระบบจะแปลงเป็น kips เพื่อหาค่า LEF ให้โดยอัตโนมัติ")
    
    # Conversion Factor: 1 Tonne = 2.20462 kips
    TON_TO_KIPS = 2.20462
    
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        st.subheader("Single Axle (เพลาเดี่ยว)")
        s_ton = st.number_input("น้ำหนักเพลาเดี่ยว (Tons)", value=8.2, step=0.5, help="มาตรฐานคือ 8.2 ตัน")
        s_count = st.number_input("จำนวนเพลาเดี่ยวบนรถ", value=1, min_value=0)
        s_kips = s_ton * TON_TO_KIPS
        ealf_s = (s_kips / 18)**4 * s_count # มาตรฐานเพลาเดี่ยว 18 kips
        st.caption(f"Equivalent to {s_kips:.2f} kips")
        
    with col_a2:
        st.subheader("Tandem Axle (เพลาคู่)")
        t_ton = st.number_input("น้ำหนักเพลาคู่ (Tons)", value=15.0, step=0.5, help="มาตรฐานคือ 15 ตัน")
        t_count = st.number_input("จำนวนเพลาคู่บนรถ", value=1, min_value=0)
        t_kips = t_ton * TON_TO_KIPS
        ealf_t = (t_kips / 33.2)**4 * t_count # มาตรฐานเพลาคู่ 33.2 kips
        st.caption(f"Equivalent to {t_kips:.2f} kips")
        
    with col_a3:
        st.subheader("Tridem Axle (เพลาสาม)")
        tr_ton = st.number_input("น้ำหนักเพลาสาม (Tons)", value=21.0, step=0.5)
        tr_count = st.number_input("จำนวนเพลาสามบนรถ", value=0, min_value=0)
        tr_kips = tr_ton * TON_TO_KIPS
        ealf_tr = (tr_kips / 45.4)**4 * tr_count # มาตรฐานเพลาสาม 45.4 kips
        st.caption(f"Equivalent to {tr_kips:.2f} kips")

    custom_tf = ealf_s + ealf_t + ealf_tr
    st.info(f"🚚 **Truck Factor (TF) ที่คำนวณได้: {custom_tf:.4f}**")

# --- 4. Step 2: Traffic ESALs ---
st.header("Step 2: ปริมาณจราจร (Traffic)")
t_col1, t_col2 = st.columns(2)
with t_col1:
    aadt_truck = st.number_input("ปริมาณรถบรรทุกเฉลี่ยต่อวัน (AADT_truck)", value=1000)
    tf_final = custom_tf
with t_col2:
    growth = st.number_input("อัตราเพิ่มจราจร Growth Rate (%)", value=3.0) / 100
    period = st.number_input("อายุการใช้งาน (ปี)", value=20)
    gf = ((1 + growth)**period - 1) / growth
    lane_dist = st.slider("Lane Distribution (DL)", 0.1, 1.0, 0.5)

w18 = aadt_truck * tf_final * 365 * gf * lane_dist
st.success(f"📈 **Total Design ESALs (W18): {w18:,.0f}**")

# --- 5. Step 3: Design Parameters (Sidebar) ---
st.sidebar.header("Design Parameters")
p_type = st.sidebar.selectbox("Pavement Type", ["Flexible (AC)", "Rigid (Concrete)"])
rel = st.sidebar.selectbox("Reliability (R%)", [85, 90, 95, 99], index=2)
ZR = {85: -1.037, 90: -1.282, 95: -1.645, 99: -2.327}[rel]
So = st.sidebar.slider("Overall Std. Deviation (So)", 0.3, 0.5, 0.45 if p_type=="Flexible (AC)" else 0.35)
pi = st.sidebar.number_input("Initial Serviceability (pi)", value=4.2 if p_type=="Flexible (AC)" else 4.5)
pt = st.sidebar.number_input("Terminal Serviceability (pt)", value=2.5)

# --- 6. Step 4: Layer Design ---
st.header(f"Step 3: ออกแบบความหนา ({p_type})")
d_col1, d_col2 = st.columns(2)

if p_type == "Flexible (AC)":
    with d_col1:
        cbr = st.number_input("Subgrade CBR (%)", value=5.0)
        mr = 1500 * cbr
        a1, a2, a3 = st.number_input("a1 (Surface)", 0.44), st.number_input("a2 (Base)", 0.14), st.number_input("a3 (Subbase)", 0.11)
        m2, m3 = st.number_input("m2", 1.0), st.number_input("m3", 1.0)
    with d_col2:
        sn_req = fsolve(aashto_flexible, 3.0, args=(ZR, So, w18, pi-pt, mr))[0]
        st.write(f"### Required Structural Number (SN): {sn_req:.3f}")
        d1_cm = st.number_input("D1 (Asphalt) [cm]", value=10.0)
        d2_cm = st.number_input("D2 (Base) [cm]", value=15.0)
        d3_cm = st.number_input("D3 (Subbase) [cm]", value=20.0)
        
        # Convert cm to inch for SN Calculation (1 inch = 2.54 cm)
        sn_prov = a1*(d1_cm/2.54) + a2*(d2_cm/2.54)*m2 + a3*(d3_cm/2.54)*m3
        st.metric("SN Provided", f"{sn_prov:.3f}", delta=f"{sn_prov - sn_req:.3f}")
else:
    with d_col1:
        sc = st.number_input("Modulus of Rupture (psi)", value=650)
        ec = st.number_input("Modulus of Elasticity (psi)", value=4000000)
        k = st.number_input("k-value (pci)", value=150)
        j = st.number_input("Load Transfer (J)", value=3.2)
        cd = st.number_input("Drainage (Cd)", value=1.0)
    with d_col2:
        d_req_in = fsolve(aashto_rigid, 8.0, args=(ZR, So, w18, pi-pt, sc, cd, j, ec, k))[0]
        d_req_cm = d_req_in * 2.54
        st.write(f"### Required Thickness: {d_req_cm:.2f} cm")
        d_in_cm = st.number_input("Design Slab Thickness [cm]", value=float(np.ceil(d_req_cm)))
        d_in = d_in_cm / 2.54

# --- Final Result ---
if (p_type=="Flexible (AC)" and sn_prov >= sn_req) or (p_type=="Rigid (Concrete)" and d_in_cm >= d_req_cm):
    st.balloons()
    st.success("✅ โครงสร้างผ่านเกณฑ์ (Design Satisified)")
else:
    st.error("❌ โครงสร้างไม่เพียงพอ (Design Inadequate)")
