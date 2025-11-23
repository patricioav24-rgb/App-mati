import streamlit as st
import pandas as pd
import math
from datetime import datetime, date, time

# ===============================================
# BASE DE RADIONÚCLIDOS
# ===============================================

RADIONUCLIDOS_DB = {
    "Tc-99m (MDP/HDP)": {
        "half_life_hr": 6.01,
        "A0_vial_mbq": 37000.0,
        "default_conc": 100.0,
        "dose_typical_mbq": 900.0,
        "dose_type": "fija",
        "notes": "Gammagrafía ósea adulto: 740–1110 MBq"
    },
    "F-18 (FDG)": {
        "half_life_hr": 1.8295,
        "A0_vial_mbq": 7400.0,
        "default_conc": 370.0,
        "dose_typical_mbq_per_kg": 4.0,
        "dose_type": "por_kg",
        "notes": "PET FDG: 3.7–5.2 MBq/kg"
    },
    "Ga-68 (PSMA/DOTATATE)": {
        "half_life_hr": 1.128,
        "A0_vial_mbq": 1200.0,
        "default_conc": 200.0,
        "dose_typical_mbq": 150.0,
        "dose_type": "fija",
        "notes": "Ga-68: 100–200 MBq"
    },
    "I-131 (diagnóstico)": {
        "half_life_hr": 8.02 * 24,
        "A0_vial_mbq": 740.0,
        "default_conc": 74.0,
        "dose_typical_mbq": 150.0,
        "dose_type": "fija",
        "notes": "100–200 MBq"
    },
    "I-131 (terapia)": {
        "half_life_hr": 8.02 * 24,
        "A0_vial_mbq": 3700.0,
        "default_conc": 74.0,
        "dose_typical_mbq": 3700.0,
        "dose_type": "fija",
        "notes": "Dosis terapéuticas"
    },
    "Personalizado": {
        "half_life_hr": None,
        "A0_vial_mbq": None,
        "default_conc": None,
        "dose_typical_mbq": None,
        "dose_type": None,
        "notes": "Ingrese manualmente"
    }
}

# ===============================================
# FUNCIONES
# ===============================================

def obtener_lambda(T_half_hrs):
    T_half_min = T_half_hrs * 60
    return math.log(2) / T_half_min

def actividad_con_decadencia(A0_mbq, T_half_hrs, t_min):
    lam = obtener_lambda(T_half_hrs)
    return A0_mbq * math.exp(-lam * t_min)

# ===============================================
# INTERFAZ STREAMLIT
# ===============================================

st.title("🧪 NucleoCalc — Calculadora de Decaimiento Radiactivo")

rad = st.selectbox("Radionúclido:", list(RADIONUCLIDOS_DB.keys()))

data = RADIONUCLIDOS_DB[rad]

col1, col2, col3 = st.columns(3)

with col1:
    A0 = st.number_input("A₀ vial (MBq):", value=data["A0_vial_mbq"] if data["A0_vial_mbq"] else 0.0)

with col2:
    T_half = st.number_input("T½ (horas):", value=data["half_life_hr"] if data["half_life_hr"] else 0.0)

with col3:
    conc = st.number_input("Concentración (MBq/mL):", value=data["default_conc"] if data["default_conc"] else 0.0)

# Tiempo
st.subheader("⏱️ Tiempos")

colA, colB = st.columns(2)

with colA:
    prep_date = st.date_input("Fecha preparación:", value=date.today())
    prep_time = st.time_input("Hora preparación:", value=datetime.now().time())

with colB:
    now_date = st.date_input("Fecha actual:", value=date.today())
    now_time = st.time_input("Hora actual:", value=datetime.now().time())

prep_dt = datetime.combine(prep_date, prep_time)
now_dt = datetime.combine(now_date, now_time)

delta_min = (now_dt - prep_dt).total_seconds() / 60

# Dosis
st.subheader("💉 Dosis")

modo = st.radio("Tipo de dosis:", ["Típica", "MBq/kg", "Fija"])

if modo == "MBq/kg":
    mbqkg = st.number_input("MBq/kg:", value=4.0)
    peso = st.number_input("Peso paciente (kg):", value=70.0)
    dosis = mbqkg * peso

elif modo == "Fija":
    dosis = st.number_input("Dosis fija (MBq):", value=900.0)

else:
    if data["dose_type"] == "fija":
        dosis = data["dose_typical_mbq"]
    else:
        peso = st.number_input("Peso (kg):", value=70.0)
        dosis = data["dose_typical_mbq_per_kg"] * peso

# ===============================================
# CÁLCULOS
# ===============================================

if st.button("Calcular"):
    lam = obtener_lambda(T_half)
    At = actividad_con_decadencia(A0, T_half, delta_min)

    vol_px = dosis / conc
    vol_total = At / conc
    pacientes_posibles = int(At // dosis)

    st.subheader("📊 Resultados")

    st.write(f"**Actividad actual A(t):** {At:.2f} MBq")
    st.write(f"**λ:** {lam:.6e} (min⁻¹)")
    st.write(f"**Tiempo transcurrido:** {delta_min:.1f} min")
    st.write("---")
    st.write(f"**Dosis paciente:** {dosis:.2f} MBq")
    st.write(f"**Volumen por paciente:** {vol_px:.2f} mL")
    st.write(f"**Volumen total disponible:** {vol_total:.2f} mL")
    st.write(f"**Pacientes posibles:** {pacientes_posibles}")
    st.write("---")

    st.latex(r"\lambda = \frac{\ln(2)}{T_{1/2}}")
    st.latex(fr"T_{{1/2}} = {T_half} \text{{ h}} = {T_half*60:.2f} \text{{ min}}")
    st.latex(fr"\lambda = \frac{{0.693}}{{{T_half*60:.2f}}}")
    st.latex(fr"A(t) = {A0} \, e^{{-{lam:.6e} \cdot {delta_min:.1f}}} = {At:.2f}")

