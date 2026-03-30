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

# --- 5. การคำนวณตามประเภท (Step 4 & 5) ---
if "Flexible" in pavement_type:
    st.header("Step 4: Layer Material & Calculation")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.subheader("Material Properties")
        cbr = st.number_input("Subgrade CBR (%)", value=5.0)
        mr = 1500 * cbr
        a1 = st.number_input("a1 (Asphalt Layer)", value=0.44)
        a2 = st.number_input("a2 (Base Layer)", value=0.14)
        m2 = st.number_input("m2 (Drainage Base)", value=1.0)
        a3 = st.number_input("a3 (Subbase Layer)", value=0.11)
        m3 = st.number_input("m3 (Drainage Subbase)", value=1.0)
    
    with m_col2:
        st.subheader("Thickness Selection")
        sn_req = fsolve(aashto_flexible, 3.0, args=(ZR, So, w18, delta_PSI, mr))[0]
        st.write(f"### Required SN: :blue[{sn_req:.3f}]")
        
        d1 = st.number_input("Thickness D1 (Asphalt) [inch]", value=4.0)
        d2 = st.number_input("Thickness D2 (Base) [inch]", value=6.0)
        d3 = st.number_input("Thickness D3 (Subbase) [inch]", value=8.0)
        
        sn_prov = (a1*d1) + (a2*d2*m2) + (a3*d3*m3)
        st.metric("Total SN Provided", f"{sn_prov:.3f}", delta=f"{sn_prov - sn_req:.3f}")
        
        if sn_prov >= sn_req: st.success("✅ โครงสร้างผ่านเกณฑ์")
        else: st.error("❌ โครงสร้างไม่เพียงพอ")

else:
    st.header("Step 4: Rigid Pavement Parameters")
    r_col1, r_col2 = st.columns(2)
    with r_col1:
        sc = st.number_input("Modulus of Rupture (Sc') [psi]", value=650)
        ec = st.number_input("Modulus of Elasticity (Ec) [psi]", value=4000000)
        k = st.number_input("Modulus of Subgrade Reaction (k) [pci]", value=150)
        j = st.number_input("Load Transfer (J)", value=3.2)
        cd = st.number_input("Drainage Coefficient (Cd)", value=1.0)
    
    with r_col2:
        d_req = fsolve(aashto_rigid, 8.0, args=(ZR, So, w18, delta_PSI, sc, cd, j, ec, k))[0]
        st.write(f"### Required Thickness (D): :blue[{d_req:.2f} inches]")
        d_input = st.number_input("Design Slab Thickness [inch]", value=float(np.ceil(d_req)))
        
        if d_input >= d_req: st.success("✅ โครงสร้างผ่านเกณฑ์")
        else: st.error("❌ โครงสร้างไม่เพียงพอ")

# --- 6. Footer & Instructions ---
st.markdown("---")
with st.expander("ℹ️ คำแนะนำการใช้งาน"):
    st.write("""
    1. **Traffic:** คำนวณ ESALs จากจำนวนรถบรรทุกเฉลี่ยต่อวัน (AADT)
    2. **MR:** คำนวณจากสูตรพื้นฐาน $M_R = 1500 \times CBR$ (หน่วย psi)
    3. **J (Load Transfer):** - มี Dowel bar: 3.2
       - ไม่มี Dowel bar: 3.8 - 4.4
    4. **Output:** ค่า SN หรือ D ที่คำนวณได้เป็นหน่วย 'นิ้ว' ตามมาตรฐาน AASHTO
    """)
