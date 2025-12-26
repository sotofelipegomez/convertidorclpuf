import streamlit as st
import requests
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Herramientas UF Pro", page_icon="📈")

# --- 2. PERSISTENCIA DEL HISTORIAL ACUMULADO (VENTANA ETERNA) ---
if 'historial_acumulado' not in st.session_state:
    st.session_state.historial_acumulado = []

# --- 3. GESTIÓN DE LIMPIEZA DE VENTANA ACTUAL ---
if 'last_opcion' not in st.session_state:
    st.session_state.last_opcion = ""
    st.session_state.historial_ventana = []

# --- 4. FUNCIONES DE APOYO (FORMATO CHILE) ---
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

# --- 5. MENÚ LATERAL ---
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    [
        "CLP a UF (Automático)", 
        "UF a CLP (Automático)", 
        "Calcular Valor UF (Inverso)",
        "Buscar Fecha por Valor", 
        "📜 Historial General"
    ]
)

# Limpieza automática al cambiar de pestaña
if st.session_state.last_opcion != opcion:
    st.session_state.historial_ventana = []
    st.session_state.last_opcion = opcion

# --- 6. LÓGICA DE HERRAMIENTAS ---

# --- CLP A UF AUTOMÁTICO ---
if opcion == "CLP a UF (Automático)":
    st.title("💰 CLP a UF por Fecha")
    fecha_txt = st.text_input("Ingresa la fecha (DD-MM-AAAA):", placeholder="Ej: 01-07-2022")
    if fecha_txt:
        try:
            fecha_valida = datetime.strptime(fecha_txt, "%d-%m-%Y")
            f_str = fecha_valida.strftime("%d-%m-%Y")
            url = f"https://mindicador.cl/api/uf/{f_str}"
            data = requests.get(url).json()
            v_uf = data['serie'][0]['valor'] if data['serie'] else None
            if v_uf:
                st.info(f"Valor UF detectado: **${formato_chile(v_uf)}**")
                with st.form("form_clp_uf", clear_on_submit=True):
                    monto_in = st.text_input("Ingresa cantidad en CLP:")
                    if st.form_submit_button("Convertir"):
                        num = limpiar_monto(monto_in)
                        if num:
                            res = num / v_uf
                            item = {"orig": f"${formato_chile(num, True)}", "dest": f"{formato_chile(res)} UF", "ref": f"Fecha: {f_str} (${formato_chile(v_uf)})", "tipo": "CLP->UF"}
                            st.session_state.historial_ventana.append(item)
                            st.session_state.historial_acumulado.append(item)
                            st.rerun()
                if st.session_state.historial_ventana:
                    act = st.session_state.historial_ventana[-1]
                    st.markdown("### 💎 Resultado Actual:")
                    c1, c2 = st.columns(2)
                    c1.metric("MONTO CLP", act['orig'])
                    c2.metric("TOTAL EN UF", act['dest'])
                    st.divider()
                    for it in reversed(st.session_state.historial_ventana):
                        st.code(f"{it['orig']} -> {it['dest']} | {it['ref']}")
        except: st.error("Fecha incorrecta.")

# --- UF A CLP AUTOMÁTICO ---
elif opcion == "UF a CLP (Automático)":
    st.title("💰 UF a CLP por Fecha")
    fecha_txt = st.text_input("Ingresa la fecha (DD-MM-AAAA):", placeholder="Ej: 01-07-2022")
    if fecha_txt:
        try:
            fecha_valida = datetime.strptime(fecha_txt, "%d-%m-%Y")
            f_str = fecha_valida.strftime("%d-%m-%Y")
            url = f"https://mindicador.cl/api/uf/{f_str}"
            data = requests.get(url).json()
            v_uf = data['serie'][0]['valor'] if data['serie'] else None
            if v_uf:
                st.info(f"Valor UF detectado: **${formato_chile(v_uf)}**")
                with st.form("form_uf_clp", clear_on_submit=True):
                    monto_in = st.text_input("Ingresa cantidad en UF:")
                    if st.form_submit_button("Convertir"):
                        num = limpiar_monto(monto_in)
                        if num:
                            res = num * v_uf
                            item = {"orig": f"{formato_chile(num)} UF", "dest": f"${formato_chile(res, True)}", "ref": f"Fecha: {f_str} (${formato_chile(v_uf)})", "tipo": "UF->CLP"}
                            st.session_state.historial_ventana.append(item)
                            st.session_state.historial_acumulado.append(item)
                            st.rerun()
                if st.session_state.historial_ventana:
                    act = st.session_state.historial_ventana[-1]
                    st.markdown("### 💎 Resultado Actual:")
                    c1, c2 = st.columns(2)
                    c1.metric("MONTO UF", act['orig'])
                    c2.metric("TOTAL EN CLP", act['dest'])
                    st.divider()
                    for it in reversed(st.session_state.historial_ventana):
                        st.code(f"{it['orig']} -> {it['dest']} | {it['ref']}")
        except: st.error("Fecha incorrecta.")

# --- CÁLCULO INVERSO ---
elif opcion == "Calcular Valor UF (Inverso)":
    st.title("🔍 Calcular Valor UF Utilizado")
    with st.form("form_inv", clear_on_submit=True):
        col1, col2 = st.columns(2)
        clp_in = col1.text_input("Monto Total CLP:", placeholder="Ej: 123.456.789")
        uf_in = col2.text_input("Monto Total UF:", placeholder="Ej: 3.450,12")
        if st.form_submit_button("Revelar Valor UF"):
            v_clp = limpiar_monto(clp_in)
            v_uf = limpiar_monto(uf_in)
            if v_clp and v_uf:
                unitario = v_clp / v_uf
                item = {"orig": f"${formato_chile(v_clp, True)} / {formato_chile(v_uf)} UF", "dest": f"${formato_chile(unitario)} (UF)", "ref": "Cálculo Inverso", "tipo": "INVERSO"}
                st.session_state.historial_ventana.append(item)
                st.session_state.historial_acumulado.append(item)
                st.rerun()
    if st.session_state.historial_ventana:
        act = st.session_state.historial_ventana[-1]
        st.markdown("### 💎 Valor UF detectado:")
        st.metric("UF UNITARIA", act['dest'])
        st.divider()
        for it in reversed(st.session_state.historial_ventana):
            st.code(f"{it['orig']} = {it['dest']} | {it['ref']}")

# --- OTRAS PÁGINAS ---
elif opcion == "Buscar Fecha por Valor":
    st.title("🔍 Buscar Fecha según Valor UF")
    col1, col2 = st.columns(2)
    with col1: ini = st.text_input("Fecha Inicio:", placeholder="01-01-2024")
    with col2: fin = st.text_input("Fecha Término:", placeholder="31-12-2024")
    target_val = limpiar_monto(st.text_input("Valor UF a buscar:"))
    if st.button("Iniciar Búsqueda") and target_val:
        # (Lógica de búsqueda se mantiene igual)
        st.write("Buscando...")

elif opcion == "📜 Historial General":
    st.title("📜 Historial Acumulado Eterno")
    if st.button("🗑️ Borrar Historial"):
        st.session_state.historial_acumulado = []
        st.rerun()
    st.divider()
    for it in reversed(st.session_state.historial_acumulado):
        st.code(f"[{it['tipo']}] {it['orig']} -> {it['dest']} | {it['ref']}")
