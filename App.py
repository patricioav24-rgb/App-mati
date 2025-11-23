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
# BASE DE RADIONÚCLIDOS (MESMA QUE TU CÓDIGO)
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
st.title("🧪 NucleoCalc — Versión Streamlit")
st.write("Cálculo con T½ en **horas** igual que tu documento.")

# -----------------------------------------------
# Selección del radionúclido
# -----------------------------------------------
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

# -----------------------------------------------
# Tiempos
# -----------------------------------------------
st.subheader("Tiempo")

# Inicializar en session_state para evitar que los valores por defecto se
# recalculen en cada rerun (eso impide que el usuario cambie la hora).
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

# -----------------------------------------------
# Dosis
# -----------------------------------------------
st.subheader("Dosis")

modo = st.radio("Modo de dosis", [
    "Usar dosis típica del radiofármaco",
    "MBq/kg (personalizado)",
    "Dosis fija (personalizada)"
])

peso = st.number_input("Peso (kg)", value=70.0)
mbqkg = st.number_input("MBq/kg", value=4.0)
fixed = st.number_input("Dosis fija (MBq)", value=900.0)

# -----------------------------------------------
# BOTÓN CALCULAR
# -----------------------------------------------
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

    # Detalle de cálculos (fórmulas aplicadas con valores)
    st.markdown("### Detalle de cálculos — fórmulas y valores aplicados")
    st.markdown(f"- T_{{1/2}} = {T_half} h = {T_half*60:.2f} min")
    st.markdown(f"- λ = ln(2) / T_{{1/2}}(min) = 0.693 / {T_half*60:.2f} = {lam:.6e} min⁻¹")
    st.markdown(f"- A(t) = A₀ · e^(-λ·t) = {A0} · e^(-{lam:.6e} · {delta_min:.1f}) = {At:.2f} MBq")
    st.markdown(f"- Volumen por paciente = dosis / concentración = {dosis:.2f} / {conc:.2f} = {vol_paciente:.2f} mL")
    st.markdown(f"- Volumen total disponible = A(t) / concentración = {At:.2f} / {conc:.2f} = {vol_total:.2f} mL")
    st.markdown(f"- Pacientes posibles = floor(A(t) / dosis) = floor({At:.2f} / {dosis:.2f}) = {pacientes}")

    # Opción: mostrar como dibujo (imagen) las fórmulas aplicadas
    if st.checkbox("Mostrar cálculo como dibujo", value=True):
        lines = [
            rf"$T_{{1/2}} = {T_half}~\mathrm{{h}} = {T_half*60:.2f}~\mathrm{{min}}$",
            rf"$\lambda = \ln(2)/T_{{1/2}} = 0.693/{T_half*60:.2f} = {lam:.6e}~\mathrm{{min}}^{{-1}}$",
            rf"$A(t) = A_0\,e^{{-\lambda t}} = {A0}\,e^{{-{lam:.6e}\cdot {delta_min:.1f}}} = {At:.2f}\,\mathrm{{MBq}}$",
            rf"Volumen\ por\ paciente = \dfrac{{{dosis:.2f}}}{{{conc:.2f}}} = {vol_paciente:.2f}\ \mathrm{{mL}}$",
            rf"Volumen\ total = \dfrac{{{At:.2f}}}{{{conc:.2f}}} = {vol_total:.2f}\ \mathrm{{mL}}$",
            rf"Pacientes\ posibles = \left\lfloor\dfrac{{{At:.2f}}}{{{dosis:.2f}}}\right\rfloor = {pacientes}$",
        ]

        if not HAS_MPL:
            st.warning("Matplotlib no está instalado. Instálalo con `pip install matplotlib` para ver el dibujo; mostrando fórmula en LaTeX en su lugar.")
            for ln in lines:
                tex = ln
                # Si la línea está delimitada con $, extraer el contenido
                if tex.startswith("$") and tex.endswith("$"):
                    tex = tex.strip("$")
                st.markdown(f"$$ {tex} $$")
        else:
            fig_height = max(2, 0.7 * len(lines))
            fig = plt.figure(figsize=(8, fig_height))
            plt.axis('off')
            y = 0.95
            for ln in lines:
                # Matplotlib no renderiza LaTeX inline perfectamente sin rc, pero esto funciona para texto
                plt.text(0.01, y, ln, fontsize=14, va='top')
                y -= 1.0 / (len(lines) + 1)

            buf = io.BytesIO()
            plt.tight_layout()
            fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            st.image(buf)
            plt.close(fig)


