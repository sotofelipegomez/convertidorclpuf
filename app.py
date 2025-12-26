import streamlit as st
import requests
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Herramientas UF Pro", page_icon="📈")

# --- 2. PERSISTENCIA DEL HISTORIAL ---
if 'historial_acumulado' not in st.session_state:
    st.session_state.historial_acumulado = []
if 'last_opcion' not in st.session_state:
    st.session_state.last_opcion = ""
    st.session_state.historial_ventana = []

# --- 3. FUNCIONES DE APOYO ---
def formato_chile(valor, es_clp=False):
    if valor is None: return ""
    decimales = 0 if es_clp else 2
    txt = f"{valor:,.{decimales}f}"
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")

def limpiar_monto(texto):
    if not texto or not texto.strip(): return None
    t = texto.strip().replace("$", "").replace(" ", "")
    if "." in t and "," in t:
        if t.rfind(".") > t.rfind(","): t = t.replace(",", "")
        else: t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        if t.count(",") > 1 or len(t.split(",")[-1]) != 2: t = t.replace(",", "")
        else: t = t.replace(",", ".")
    elif "." in t:
        if t.count(".") > 1 or len(t.split(".")[-1]) != 2: t = t.replace(".", "")
    try: return float(t)
    except: return None

# --- 4. MENÚ LATERAL ---
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    ["Conversión Dual (CLP ↔ UF)", "Calcular Valor UF (Inverso)", "📜 Historial General"]
)

if st.session_state.last_opcion != opcion:
    st.session_state.historial_ventana = []
    st.session_state.last_opcion = opcion

# --- 5. LÓGICA DE HERRAMIENTAS ---

if opcion == "Conversión Dual (CLP ↔ UF)":
    st.title("🔄 Conversión Dual CLP ↔ UF")
    
    # Obtener UF del día automáticamente
    url = f"https://mindicador.cl/api/uf"
    try:
        data = requests.get(url).json()
        valor_uf_hoy = data['serie'][0]['valor']
        st.info(f"Valor UF hoy: **${formato_chile(valor_uf_hoy)}**")
    except:
        valor_uf_hoy = 38000.0 # Valor de respaldo
        st.error("No se pudo obtener la UF en tiempo real. Usando valor referencial.")

    # --- BLOQUE 1: CLP A UF (ARRIBA) ---
    st.subheader("1. De Pesos (CLP) a UF")
    with st.form("form_clp_to_uf", clear_on_submit=True):
        monto_clp_in = st.text_input("Monto en CLP:", placeholder="Ej: 1.000.000")
        if st.form_submit_button("Convertir a UF ⬇️"):
            val = limpiar_monto(monto_clp_in)
            if val:
                res = val / valor_uf_hoy
                item = {"clp": val, "uf": res, "ref": f"CLP a UF (UF: ${formato_chile(valor_uf_hoy)})", "tipo": "CLP->UF"}
                st.session_state.historial_ventana.append(item)
                st.session_state.historial_acumulado.append(item)
                st.rerun()

    st.markdown("---")

    # --- BLOQUE 2: UF A CLP (ABAJO) ---
    st.subheader("2. De UF a Pesos (CLP)")
    with st.form("form_uf_to_clp", clear_on_submit=True):
        monto_uf_in = st.text_input("Monto en UF:", placeholder="Ej: 26,5")
        if st.form_submit_button("Convertir a CLP ⬆️"):
            val_uf = limpiar_monto(monto_uf_in)
            if val_uf:
                res_clp = val_uf * valor_uf_hoy
                item = {"clp": res_clp, "uf": val_uf, "ref": f"UF a CLP (UF: ${formato_chile(valor_uf_hoy)})", "tipo": "UF->CLP"}
                st.session_state.historial_ventana.append(item)
                st.session_state.historial_acumulado.append(item)
                st.rerun()

    # Mostrar Resultados de la ventana actual
    if st.session_state.historial_ventana:
        st.divider()
        st.markdown("### 💎 Últimos Cálculos Realizados:")
        actual = st.session_state.historial_ventana[-1]
        c1, c2 = st.columns(2)
        c1.metric("MONTO CLP", f"${formato_chile(actual['clp'], True)}")
        c2.metric("MONTO UF", f"{formato_chile(actual['uf'])} UF")
        
        for it in reversed(st.session_state.historial_ventana):
            st.code(f"[{it['tipo']}] {formato_chile(it['clp'], True)} CLP ↔ {formato_chile(it['uf'])} UF")

elif opcion == "Calcular Valor UF (Inverso)":
    st.title("🔍 Calcular Valor UF Utilizado")
    with st.form("form_inverso", clear_on_submit=True):
        c1, c2 = st.columns(2)
        clp_in = c1.text_input("Total CLP:", placeholder="123.456.789")
        uf_in = c2.text_input("Total UF:", placeholder="3.450,12")
        if st.form_submit_button("Revelar Valor UF"):
            v_clp = limpiar_monto(clp_in)
            v_uf = limpiar_monto(uf_in)
            if v_clp and v_uf:
                unitario = v_clp / v_uf
                item = {"clp": v_clp, "uf": v_uf, "res_unitario": unitario, "tipo": "INVERSO"}
                st.session_state.historial_ventana.append(item)
                st.session_state.historial_acumulado.append(item)
                st.rerun()

    if st.session_state.historial_ventana:
        act = st.session_state.historial_ventana[-1]
        st.metric("UF DETECTADA", f"${formato_chile(act['res_unitario'])}")
        st.write(f"Cálculo: {formato_chile(act['clp'], True)} / {formato_chile(act['uf'])}")

elif opcion == "📜 Historial General":
    st.title("📜 Historial General")
    if st.button("Limpiar Todo"):
        st.session_state.historial_acumulado = []
        st.rerun()
    for it in reversed(st.session_state.historial_acumulado):
        if it.get('tipo') == "INVERSO":
            st.write(f"📌 **Inverso:** UF ${formato_chile(it['res_unitario'])} (de {formato_chile(it['clp'],True)} CLP / {formato_chile(it['uf'])} UF)")
        else:
            st.write(f"📌 **{it['tipo']}:** {formato_chile(it['clp'],True)} CLP ↔ {formato_chile(it['uf'])} UF")
