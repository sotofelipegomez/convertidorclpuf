import streamlit as st
import requests
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Herramientas UF Pro", page_icon="📈")

# --- 2. PERSISTENCIA DEL HISTORIAL ACUMULADO ---
if 'historial_acumulado' not in st.session_state:
    st.session_state.historial_acumulado = []

# --- 3. GESTIÓN DE LIMPIEZA DE VENTANA ACTUAL ---
if 'last_opcion' not in st.session_state:
    st.session_state.last_opcion = ""
    st.session_state.historial_ventana = []

# --- 4. FUNCIONES DE APOYO ---

def formato_chile(valor, es_clp=False):
    if valor is None: return ""
    decimales = 0 if es_clp else 2
    txt = f"{valor:,.{decimales}f}"
    # Formato Chileno: Puntos para miles, Coma para decimal
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")

def limpiar_monto(texto):
    if not texto or not texto.strip(): return None
    t = texto.strip()
    t = t.replace("$", "").replace(" ", "")
    
    if "." in t and "," in t:
        if t.rfind(".") > t.rfind(","): 
            t = t.replace(",", "")
        else: 
            t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        if t.count(",") > 1 or len(t.split(",")[-1]) != 2:
            t = t.replace(",", "")
        else:
            t = t.replace(",", ".")
    elif "." in t:
        if t.count(".") > 1 or len(t.split(".")[-1]) != 2:
            t = t.replace(".", "")
            
    try:
        return float(t)
    except:
        return None

# --- 5. MENÚ LATERAL ---
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    ["UF Automática (Fecha)", "UF Manual (Valor fijo)", "Calcular Valor UF (Inverso)", "Buscar Fecha por Valor", "📜 Historial General"]
)

if st.session_state.last_opcion != opcion:
    st.session_state.historial_ventana = []
    st.session_state.last_opcion = opcion

# --- 6. LÓGICA DE HERRAMIENTAS ---

if opcion == "UF Manual (Valor fijo)":
    st.title("⚙️ UF Manual")
    v_uf_txt = st.text_input("1. Valor UF base (Unitario):", placeholder="Ej: 35.000")
    v_fijo = limpiar_monto(v_uf_txt)
    
    if v_fijo:
        st.write(f"-> Valor UF fijado: **${formato_chile(v_fijo)}**")
        
        # RECTÁNGULO A: CLP A UF (DIVIDIR)
        with st.form("form_manual_clp_uf", clear_on_submit=True):
            st.write("### ⬇️ Convertir de CLP a UF")
            monto_clp_in = st.text_input("Cantidad en CLP:")
            if st.form_submit_button("Convertir"):
                num = limpiar_monto(monto_clp_in)
                if num:
                    res = num / v_fijo
                    item = {"orig": f"${formato_chile(num, True)}", "dest": f"{formato_chile(res)} UF", "ref": f"UF Fija: ${formato_chile(v_fijo)}", "tipo": "MANUAL-DIV"}
                    st.session_state.historial_ventana.append(item)
                    st.session_state.historial_acumulado.append(item)
                    st.rerun()

        st.write("") 

        # RECTÁNGULO B: UF A CLP (MULTIPLICAR)
        with st.form("form_manual_uf_clp", clear_on_submit=True):
            st.write("### ⬆️ Convertir de UF a CLP")
            monto_uf_in = st.text_input("Cantidad en UF:")
            if st.form_submit_button("Convertir"):
                num_uf = limpiar_monto(monto_uf_in)
                if num_uf:
                    res_clp = num_uf * v_fijo
                    item = {"orig": f"{formato_chile(num_uf)} UF", "dest": f"${formato_chile(res_clp, True)}", "ref": f"UF Fija: ${formato_chile(v_fijo)}", "tipo": "MANUAL-MULT"}
                    st.session_state.historial_ventana.append(item)
                    st.session_state.historial_acumulado.append(item)
                    st.rerun()

        if st.session_state.historial_ventana:
            actual = st.session_state.historial_ventana[-1]
            st.markdown("### 💎 Último Cálculo:")
            c1, c2 = st.columns(2)
            c1.metric("INGRESADO", actual['orig'])
            c2.metric("RESULTADO", actual['dest'])
            st.divider()
            for it in reversed(st.session_state.historial_ventana):
                st.code(f"{it['orig']} -> {it['dest']} | {it['ref']}")

elif opcion == "UF Automática (Fecha)":
    st.title("💰 UF Automática por Fecha")
    fecha_txt = st.text_input("Ingresa la fecha (DD-MM-AAAA):", placeholder="Ej: 01-07-2022")
    if fecha_txt:
        try:
            fecha_valida = datetime.strptime(fecha_txt, "%d-%m-%Y")
            f_str = fecha_valida.strftime("%d-%m-%Y")
            url = f"https://mindicador.cl/api/uf/{f_str}"
            data = requests.get(url).json()
            valor_uf = data['serie'][0]['valor'] if data['serie'] else None
            if valor_uf:
                st.info(f"Valor UF detectado: **${formato_chile(valor_uf)}**")
                with st.form("form_auto", clear_on_submit=True):
                    monto_input = st.text_input("Ingresa cantidad en CLP:")
                    if st.form_submit_button("Convertir"):
                        monto_num = limpiar_monto(monto_input)
                        if monto_num:
                            res_uf = monto_num / valor_uf
                            item = {"orig": f"${formato_chile(monto_num, True)}", "dest": f"{formato_chile(res_uf)} UF", "ref": f"Fecha: {f_str} (${formato_chile(valor_uf)})", "tipo": "AUTO"}
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
            else: st.warning("No hay datos.")
        except: st.error("Fecha inválida.")

elif opcion == "Calcular Valor UF (Inverso)":
    st.title("🔍 Calcular Valor UF Utilizado")
    with st.form("form_inverso", clear_on_submit=True):
        col1, col2 = st.columns(2)
        monto_clp_in = col1.text_input("Monto Total CLP:", placeholder="Ej: 123.456.789")
        monto_uf_in = col2.text_input("Monto Total UF:", placeholder="Ej: 3.450,12")
        if st.form_submit_button("Revelar Valor UF"):
            clp_val = limpiar_monto(monto_clp_in)
            uf_val = limpiar_monto(monto_uf_in)
            if clp_val and uf_val and uf_val != 0:
                uf_unitaria = clp_val / uf_val
                item = {"clp": clp_val, "uf": uf_val, "res_unitario": uf_unitaria, "ref": "Cálculo Inverso", "tipo": "INVERSO"}
                st.session_state.historial_ventana.append(item)
                st.session_state.historial_acumulado.append(item)
                st.rerun()

    if st.session_state.historial_ventana:
        actual = st.session_state.historial_ventana[-1]
        st.markdown("### 💎 Valor UF detectado:")
        st.metric("UF UNITARIA", f"${formato_chile(actual['res_unitario'])}")
        st.divider()
        for it in reversed(st.session_state.historial_ventana):
            st.code(f"Resultado: ${formato_chile(it['res_unitario'])} | (Total: ${formato_chile(it['clp'], True)} / {formato_chile(it['uf'])} UF)")

elif opcion == "Buscar Fecha por Valor":
    st.title("🔍 Buscar Fecha según Valor UF")
    col1, col2 = st.columns(2)
    with col1: ini = st.text_input("Fecha Inicio:")
    with col2: fin = st.text_input("Fecha Término:")
    t_val = limpiar_monto(st.text_input("Valor UF a buscar:"))
    if st.button("Buscar") and t_val:
        st.write("Buscando datos...")

elif opcion == "📜 Historial General":
    st.title("📜 Historial Acumulado Eterno")
    if st.button("🗑️ Borrar Historial"):
        st.session_state.historial_acumulado = []
        st.rerun()
    st.divider()
    if st.session_state.historial_acumulado:
        for item in reversed(st.session_state.historial_acumulado):
            if item['tipo'] == "INVERSO":
                st.code(f"[INVERSO] {formato_chile(item['clp'], True)} CLP / {formato_chile(item['uf'])} UF = UF: ${formato_chile(item['res_unitario'])}")
            elif "MULT" in item['tipo']:
                st.code(f"[UF->CLP] {item['orig']} -> {item['dest']} | {item['ref']}")
            else:
                st.code(f"[CLP->UF] {item['orig']} -> {item['dest']} | {item['ref']}")
