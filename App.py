import streamlit as st
import math
import io
try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except Exception:
    plt = None
    HAS_MPL = False
from datetime import datetime

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
        "notes": "I-131 diagnóstico"
    },
    "I-131 (terapia)": {
        "half_life_hr": 8.02 * 24,
        "A0_vial_mbq": 3700.0,
        "default_conc": 74.0,
        "dose_typical_mbq": 3700.0,
        "dose_type": "fija",
        "notes": "I-131 terapia"
    },
    "Personalizado": {
        "half_life_hr": None,
        "A0_vial_mbq": None,
        "default_conc": None,
        "dose_typical_mbq": None,
        "dose_type": None,
        "notes": "Ingrese valores manualmente"
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
# APP STREAMLIT
# ===============================================
st.title("🧪 NucleoCalc ")
st.write("Cálculo con T½ en **horas** igual que tu documento.")

# Selección del radionúclido
radion = st.selectbox("Radionúclido", list(RADIONUCLIDOS_DB.keys()))
data = RADIONUCLIDOS_DB[radion]

col1, col2, col3 = st.columns(3)

with col1:
    A0 = st.number_input("A₀ vial (MBq)", value=data["A0_vial_mbq"] or 0.0)
with col2:
    T_half = st.number_input("T½ (horas)", value=data["half_life_hr"] or 0.0)
with col3:
    conc = st.number_input("Concentración (MBq/mL)", value=data["default_conc"] or 1.0)

st.markdown(f"**Notas:** {data['notes']}")

# Tiempos (session_state estable)
if 'prep_date' not in st.session_state:
    st.session_state['prep_date'] = datetime.utcnow().date()
if 'prep_time' not in st.session_state:
    st.session_state['prep_time'] = datetime.utcnow().time().replace(second=0, microsecond=0)
if 'use_now' not in st.session_state:
    st.session_state['use_now'] = True
if 'now_date' not in st.session_state:
    st.session_state['now_date'] = datetime.utcnow().date()
if 'now_time' not in st.session_state:
    st.session_state['now_time'] = datetime.utcnow().time().replace(second=0, microsecond=0)

prep_date = st.date_input("Fecha de preparación", value=st.session_state['prep_date'], key='prep_date')
prep_time = st.time_input("Hora de preparación", value=st.session_state['prep_time'], key='prep_time')
prep_dt = datetime.combine(prep_date, prep_time)

use_now = st.checkbox("Usar hora actual UTC", value=st.session_state['use_now'], key='use_now')
if use_now:
    now_dt = datetime.utcnow()
else:
    now_date = st.date_input("Fecha actual", value=st.session_state['now_date'], key='now_date')
    now_time = st.time_input("Hora actual", value=st.session_state['now_time'], key='now_time')
    now_dt = datetime.combine(now_date, now_time)

delta_min = (now_dt - prep_dt).total_seconds() / 60

# Dosis
st.subheader("Dosis")
modo = st.radio("Modo de dosis", [
    "Usar dosis típica del radiofármaco",
    "MBq/kg (personalizado)",
    "Dosis fija (personalizada)"
])

peso = st.number_input("Peso (kg)", value=70.0)
mbqkg = st.number_input("MBq/kg", value=4.0)
fixed = st.number_input("Dosis fija (MBq)", value=900.0)

# BOTÓN CALCULAR
if st.button("Calcular"):

    lam = obtener_lambda(T_half)
    At = actividad_con_decadencia(A0, T_half, delta_min)

    # Dosis final
    if modo == "Usar dosis típica del radiofármaco":
        if data["dose_type"] == "fija":
            dosis = data["dose_typical_mbq"]
        else:
            dosis = data["dose_typical_mbq_per_kg"] * peso
    elif modo == "MBq/kg (personalizado)":
        dosis = mbqkg * peso
    else:
        dosis = fixed

    vol_paciente = dosis / conc
    vol_total = At / conc
    pacientes = int(At // dosis)

    st.success("Cálculo realizado correctamente")

    st.subheader("Resultados")
    st.write(f"**λ (min⁻¹):** {lam:.6e}")
    st.write(f"**Tiempo transcurrido:** {delta_min:.1f} min")
    st.write(f"**Actividad A(t):** {At:.2f} MBq")
    st.write("---")
    st.write(f"**Dosis por paciente:** {dosis:.1f} MBq")
    st.write(f"**Volumen por paciente:** {vol_paciente:.2f} mL")
    st.write(f"**Volumen total disponible:** {vol_total:.2f} mL")
    st.write(f"**Pacientes posibles:** {pacientes}")

    # === LÍNEAS CON FÓRMULAS ===
    lines = [
        rf"$T_{{1/2}} = {T_half}~h = {T_half*60:.2f}~min$",
        rf"$\lambda = \ln(2)/T_{{1/2}} = 0.693/{T_half*60:.2f} = {lam:.6e}~min^{{-1}}$",
        rf"$A(t) = A_0 e^{{-\lambda t}} = {A0}\, e^{{-{lam:.6e}\cdot {delta_min:.1f}}} = {At:.2f}~MBq$",
        rf"$Vol_{{pac}} = {dosis:.2f}/{conc:.2f} = {vol_paciente:.2f}~mL$",
        rf"$Vol_{{total}} = {At:.2f}/{conc:.2f} = {vol_total:.2f}~mL$",
        rf"$Pacientes = \left\lfloor {At:.2f}/{dosis:.2f} \right\rfloor = {pacientes}$"
    ]

    # === DIBUJO ESTILO PIZARRÓN ===
    if HAS_MPL:
        st.subheader(" Cálculo ")

        fig_height = max(3, 0.8 * len(lines))
        fig = plt.figure(figsize=(10, fig_height))

        # Fondo negro estilo pizarra
        fig.patch.set_facecolor("#1a1a1a")

        ax = fig.add_subplot(111)
        ax.set_facecolor("#1a1a1a")
        ax.axis('off')

        y = 0.95
        for ln in lines:
            ax.text(
                0.02, y, ln,
                fontsize=22,
                color="white",
                va='top'
            )
            y -= 1.1 / (len(lines) + 1)

        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=180, bbox_inches='tight', facecolor=fig.get_facecolor())
        buf.seek(0)
        st.image(buf)
        plt.close(fig)
    else:
        st.warning("Matplotslib no está instalado. Instálalo con: pip install matplotlib")
