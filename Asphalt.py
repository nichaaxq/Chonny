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
st.set_page_config(page_title="Pavement Design Pro", layout="wide")
st.title("🛣️ AASHTO 1993: Full Axle Load & Pavement Design")

# --- 3. Step 1: Custom Truck Factor Calculator ---
st.header("Step 1: Custom Truck Factor Analysis")
with st.expander("เปิดส่วนคำนวณ Truck Factor จากน้ำหนักลงเพลา (Axle Load)", expanded=False):
    st.write("คำนวณหาค่า TF โดยอ้างอิงเพลามาตรฐาน 18,000 lb (80 kN)")
    
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        st.subheader("Single Axle (เพลาเดี่ยว)")
        s_load = st.number_input("Weight per Single Axle (lb)", value=18000, step=1000)
        s_count = st.number_input("Number of Single Axles on Truck", value=1, min_value=0)
        ealf_s = (s_load / 18000)**4 * s_count
        
    with col_a2:
        st.subheader("Tandem Axle (เพลาคู่)")
        t_load = st.number_input("Weight per Tandem Axle (lb)", value=32000, step=1000)
        t_count = st.number_input("Number of Tandem Axles on Truck", value=1, min_value=0)
        ealf_t = (t_load / 33200)**4 * t_count # 33.2k คือค่ามาตรฐาน Tandem
        
    with col_a3:
        st.subheader("Tridem Axle (เพลาสาม)")
        tr_load = st.number_input("Weight per Tridem Axle (lb)", value=48000, step=1000)
        tr_count = st.number_input("Number of Tridem Axles on Truck", value=0, min_value=0)
        ealf_tr = (tr_load / 45400)**4 * tr_count

    custom_tf = ealf_s + ealf_t + ealf_tr
    st.info(f"🚚 Calculated Truck Factor (TF) for this vehicle: **{custom_tf:.4f}**")

# --- 4. Step 2: Traffic ESALs ---
st.header("Step 2: Traffic Estimation")
t_col1, t_col2 = st.columns(2)
with t_col1:
    aadt_truck = st.number_input("Total Trucks per Day (AADT_truck)", value=500)
    use_custom_tf = st.checkbox("Use Calculated Truck Factor from Step 1", value=True)
    tf_final = custom_tf if use_custom_tf else st.number_input("Manual Truck Factor", value=1.5)
with t_col2:
    growth = st.number_input("Growth Rate (%)", value=3.0) / 100
    period = st.number_input("Design Life (Years)", value=20)
    gf = ((1 + growth)**period - 1) / growth
    lane_dist = st.slider("Lane Distribution Factor", 0.1, 1.0, 0.5)

w18 = aadt_truck * tf_final * 365 * gf * lane_dist
st.success(f"📈 Total Design ESALs (W18): **{w18:,.0f}**")

# --- 5. Step 3: Design Parameters (Sidebar) ---
st.sidebar.header("Design Parameters")
p_type = st.sidebar.selectbox("Pavement Type", ["Flexible (AC)", "Rigid (Concrete)"])
rel = st.sidebar.selectbox("Reliability (R%)", [85, 90, 95, 99], index=2)
ZR = {85: -1.037, 90: -1.282, 95: -1.645, 99: -2.327}[rel]
So = st.sidebar.slider("Overall Std. Deviation (So)", 0.3, 0.5, 0.45 if p_type=="Flexible (AC)" else 0.35)
pi = st.sidebar.number_input("Initial Serviceability (pi)", value=4.2 if p_type=="Flexible (AC)" else 4.5)
pt = st.sidebar.number_input("Terminal Serviceability (pt)", value=2.5)

# --- 6. Step 4: Layer Design ---
st.header(f"Step 3: {p_type} Structure Design")
d_col1, d_col2 = st.columns(2)

if p_type == "Flexible (AC)":
    with d_col1:
        cbr = st.number_input("Subgrade CBR (%)", value=5.0)
        mr = 1500 * cbr
        a1, a2, a3 = st.number_input("a1", 0.44), st.number_input("a2", 0.14), st.number_input("a3", 0.11)
        m2, m3 = st.number_input("m2", 1.0), st.number_input("m3", 1.0)
    with d_col2:
        sn_req = fsolve(aashto_flexible, 3.0, args=(ZR, So, w18, pi-pt, mr))[0]
        st.write(f"### Required SN: {sn_req:.3f}")
        d1 = st.number_input("D1 (Asphalt) [in]", value=4.0)
        d2 = st.number_input("D2 (Base) [in]", value=6.0)
        d3 = st.number_input("D3 (Subbase) [in]", value=10.0)
        sn_prov = a1*d1 + a2*d2*m2 + a3*d3*m3
        st.metric("SN Provided", f"{sn_prov:.3f}", delta=f"{sn_prov - sn_req:.3f}")
else:
    with d_col1:
        sc = st.number_input("Modulus of Rupture (psi)", value=650)
        ec = st.number_input("Modulus of Elasticity (psi)", value=4000000)
        k = st.number_input("k-value (pci)", value=150)
        j = st.number_input("Load Transfer (J)", value=3.2)
        cd = st.number_input("Drainage (Cd)", value=1.0)
    with d_col2:
        d_req = fsolve(aashto_rigid, 8.0, args=(ZR, So, w18, pi-pt, sc, cd, j, ec, k))[0]
        st.write(f"### Required Thickness: {d_req:.2f} inches")
        d_in = st.number_input("Design Thickness [in]", value=float(np.ceil(d_req)))
        st.info(f"Actual Thickness: {d_in} in")

if (p_type=="Flexible (AC)" and sn_prov >= sn_req) or (p_type=="Rigid (Concrete)" and d_in >= d_req):
    st.balloons()
    st.success("SUCCESS: Design satisfies the requirements!")
else:
    st.error("FAIL: Design is insufficient.")
