import streamlit as st

st.title("2-Pile Eccentric Foundation Calculator")

st.header("Input")

P = st.number_input("Axial Load P (kN)", value=1000.0)
M = st.number_input("Moment M (kN-m)", value=200.0)
s = st.number_input("Pile spacing s (m)", value=2.0)

if st.button("Calculate"):

    # -----------------------
    # 1. Initial coordinates
    # -----------------------
    x1 = -s / 2
    x2 = s / 2

    # -----------------------
    # 2. Sum x^2
    # -----------------------
    sum_x2 = x1**2 + x2**2

    # -----------------------
    # 3. Reactions
    # -----------------------
    R1 = P/2 + (M * x1) / sum_x2
    R2 = P/2 + (M * x2) / sum_x2

    # -----------------------
    # 4. New centroid
    # -----------------------
    x_new = (R1*x1 + R2*x2) / (R1 + R2)

    # -----------------------
    # 5. New coordinates
    # -----------------------
    x1_new = x1 - x_new
    x2_new = x2 - x_new

    # -----------------------
    # Output
    # -----------------------
    st.subheader("Results")

    st.write("### Initial Coordinates")
    st.write(f"x1 = {x1:.3f} m")
    st.write(f"x2 = {x2:.3f} m")

    st.write("### Pile Reactions")
    st.write(f"R1 = {R1:.2f} kN")
    st.write(f"R2 = {R2:.2f} kN")

    st.write("### New Centroid")
    st.write(f"x_centroid_new = {x_new:.4f} m")

    st.write("### Adjusted Coordinates")
    st.write(f"x1_new = {x1_new:.3f} m")
    st.write(f"x2_new = {x2_new:.3f} m")

    # Checks
    st.write("### Checks")
    st.write(f"Sum of reactions = {R1 + R2:.2f} kN")

    if R1 < 0 or R2 < 0:
        st.error("⚠️ มีเสาเข็มรับแรงดึง (ต้องตรวจสอบ uplift)")
    else:
        st.success("✅ ไม่มีแรงดึงในเสาเข็ม")
