import streamlit as st
import numpy as np
from scipy.optimize import fsolve

# --- ฟังก์ชันคำนวณสำหรับ Flexible Pavement (AC) ---
def aashto_flexible(SN, ZR, So, W18, delta_PSI, MR):
    if SN < 0: return 999
    term1 = ZR * So
    term2 = 9.36 * np.log10(SN + 1) - 0.20
    term3 = np.log10(delta_PSI / (4.2 - 1.5)) / (0.40 + (1094 / (SN + 1)**5.19))
    term4 = 2.32 * np.log10(MR) - 8.07
    return term1 + term2 + term3 + term4 - np.log10(W18)

# --- ฟังก์ชันคำนวณสำหรับ Rigid Pavement (Concrete) ---
def aashto_rigid(D, ZR, So, W18, delta_PSI, Sc, Cd, J, Ec, k):
    if D <= 0: return 999
    term1 = ZR * So
    term2 = 7.35 * np.log10(D + 1) - 0.06
    term3 = np.log10(delta_PSI / (4.5 - 1.5)) / (1 + (1.624e7 / (D + 1)**8.46))
    term4 = (4.22 - 0.32 * pt) * np.log10((Sc * Cd * (D**0.75 - 1.132)) / (215.63 * J * (D**0.75 - (18.42 / (Ec / k)**0.25))))
    return term1 + term2 + term3 + term4 - np.log10(W18)

# --- ส่วนการตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Pavement Design Tool", layout="wide")
st.title("🛣️ AASHTO 1993 Pavement Design Tool")

# ส่วนเลือกประเภทผิวทาง
pavement_type = st.sidebar.selectbox("Select Pavement Type", ["Flexible Pavement (AC)", "Rigid Pavement (Concrete)"])

st.sidebar.markdown("---")
st.sidebar.header("Common Parameters")
reliability = st.sidebar.selectbox("Reliability (R, %)", [80, 85, 90, 95, 98, 99], index=3)
r_to_zr = {80: -0.841, 85: -1.037, 90: -1.282, 95: -1.645, 98: -2.054, 99: -2.327}
ZR = r_to_zr[reliability]
So = st.sidebar.number_input("Standard Deviation (So)", value=0.45 if pavement_type == "Flexible Pavement (AC)" else 0.35)
w18 = st.sidebar.number_input("Design ESALs (W18)", value=1000000, format="%d")
pi = st.sidebar.number_input("Initial Serviceability (pi)", value=4.2 if pavement_type == "Flexible Pavement (AC)" else 4.5)
pt = st.sidebar.number_input("Terminal Serviceability (pt)", value=2.5)
delta_PSI = pi - pt

# --- แยกการทำงานตามเงื่อนไข ---
if pavement_type == "Flexible Pavement (AC)":
    st.header("Flexible Pavement Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        cbr = st.number_input("Subgrade CBR (%)", value=5.0)
        mr = 1500 * cbr
        st.info(f"MR = {mr:,.0f} psi")
        a1 = st.number_input("a1 (Surface)", value=0.44)
        a2 = st.number_input("a2 (Base)", value=0.14)
        m2 = st.number_input("m2 (Drainage Base)", value=1.0)
        a3 = st.number_input("a3 (Subbase)", value=0.11)
        m3 = st.number_input("m3 (Drainage Subbase)", value=1.0)

    with col2:
        sn_req = fsolve(aashto_flexible, 3.0, args=(ZR, So, w18, delta_PSI, mr))[0]
        st.success(f"### Required SN: {sn_req:.3f}")
        d1 = st.number_input("D1 (Surface) [in]", value=4.0)
        d2 = st.number_input("D2 (Base) [in]", value=6.0)
        d3 = st.number_input("D3 (Subbase) [in]", value=8.0)
        sn_prov = (a1*d1) + (a2*d2*m2) + (a3*d3*m3)
        st.metric("SN Provided", f"{sn_prov:.3f}", delta=f"{sn_prov - sn_req:.3f}")
        if sn_prov >= sn_req: st.success("✅ ผ่าน")
        else: st.error("❌ ไม่ผ่าน")

else:
    st.header("Rigid Pavement Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        sc = st.number_input("Modulus of Rupture (S'c) [psi]", value=650)
        ec = st.number_input("Concrete Elasticity (Ec) [psi]", value=4000000)
        k = st.number_input("Modulus of Subgrade Reaction (k) [pci]", value=150)
        j = st.number_input("Load Transfer Coefficient (J)", value=3.2)
        cd = st.number_input("Drainage Coefficient (Cd)", value=1.0)

    with col2:
        # แก้สมการหาค่า D (ความหนาคอนกรีต)
        d_req = fsolve(aashto_rigid, 8.0, args=(ZR, So, w18, delta_PSI, sc, cd, j, ec, k))[0]
        st.success(f"### Required Thickness (D): {d_req:.2f} inches")
        d_input = st.number_input("Design Slab Thickness [in]", value=float(np.ceil(d_req)))
        if d_input >= d_req: st.success("✅ ผ่าน")
        else: st.error("❌ ไม่ผ่าน")
