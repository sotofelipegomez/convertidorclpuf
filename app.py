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
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")

def limpiar_monto(texto):
    if not texto or not texto.strip(): return None
    t = texto.strip()
    last_comma = t.rfind(',')
    last_dot = t.rfind('.')
    try:
        if last_comma != -1 and last_dot != -1:
            res = t.replace(".", "").replace(",", ".") if last_comma > last_dot else t.replace(",", "")
        elif last_comma != -1:
            parts = t.split(',')
            res = t.replace(",", ".") if len(parts[-1]) == 2 and len(parts) > 1 else t.replace(",", "")
        elif last_dot != -1:
            parts = t.split('.')
            res = t if len(parts[-1]) == 2 and len(parts) > 1 else t.replace(".", "")
        else:
            res = t
        return float(res)
    except: return None

# --- 5. MENÚ LATERAL ---
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    ["UF Automática (Fecha)", "UF Manual (Valor fijo)", "Buscar Fecha por Valor", "📜 Historial General"]
)

if st.session_state.last_opcion != opcion:
    st.session_state.historial_ventana = []
    st.session_state.last_opcion = opcion

# --- 6. LÓGICA DE HERRAMIENTAS ---

if opcion == "UF Automática (Fecha)":
    st.title("💰 UF Automática por Fecha")
    fecha_txt = st.text_input("Ingresa la fecha (DD-MM-AAAA):", placeholder="Ej: 01-07-2022")
    
    if fecha_txt:
        try:
            fecha_valida = datetime.strptime(fecha_txt, "%d-%m-%Y")
            fecha_str = fecha_valida.strftime("%d-%m-%Y")
            url = f"https://mindicador.cl/api/uf/{fecha_str}"
            data = requests.get(url).json()
            valor_uf = data['serie'][0]['valor'] if data['serie'] else None
            
            if valor_uf:
                st.info(f"Valor UF detectado: **${formato_chile(valor_uf)}**")
                
                with st.form("form_auto", clear_on_submit=True):
                    col_a, col_b = st.columns(2)
                    monto_clp = col_a.text_input("CLP a UF (Ingresa pesos):")
                    monto_uf = col_b.text_input("UF a CLP (Ingresa UF):")
                    enviar = st.form_submit_button("Convertir")
                    
                    if enviar:
                        res = None
                        if monto_clp:
                            num = limpiar_monto(monto_clp)
                            if num:
                                calc = num / valor_uf
                                res = {"orig": f"${formato_chile(num, True)}", "dest": f"{formato_chile(calc)} UF", "ref": f"Fecha: {fecha_str}", "tipo": "AUTO"}
                        elif monto_uf:
                            num = limpiar_monto(monto_uf)
                            if num:
                                calc = num * valor_uf
                                res = {"orig": f"{formato_chile(num)} UF", "dest": f"${formato_chile(calc, True)}", "ref": f"Fecha: {fecha_str}", "tipo": "AUTO"}
                        
                        if res:
                            st.session_state.historial_ventana.append(res)
                            st.session_state.historial_acumulado.append(res)
                            st.rerun()

                if st.session_state.historial_ventana:
                    actual = st.session_state.historial_ventana[-1]
                    st.markdown("### 💎 Resultado Actual:")
                    st.info(f"**{actual['orig']}** equivale a **{actual['dest']}**")
                    st.divider()
                    for it in reversed(st.session_state.historial_ventana):
                        st.code(f"{it['orig']} -> {it['dest']} | {it['ref']}")
            else: st.warning("No hay datos.")
        except: st.error("Error en fecha.")

elif opcion == "UF Manual (Valor fijo)":
    st.title("⚙️ UF Manual")
    uf_manual_txt = st.text_input("1. Ingresa el valor de la UF base:", placeholder="33750.00")
    valor_uf_fijo = limpiar_monto(uf_manual_txt)
    
    if valor_uf_fijo:
        st.write(f"-> Valor UF fijado: **${formato_chile(valor_uf_fijo)}**")
        with st.form("form_manual", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            monto_clp = col_a.text_input("CLP a UF:")
            monto_uf = col_b.text_input("UF a CLP:")
            if st.form_submit_button("Convertir"):
                res = None
                if monto_clp:
                    num = limpiar_monto(monto_clp)
                    if num:
                        calc = num / valor_uf_fijo
                        res = {"orig": f"${formato_chile(num, True)}", "dest": f"{formato_chile(calc)} UF", "ref": "UF Fija", "tipo": "MANUAL"}
                elif monto_uf:
                    num = limpiar_monto(monto_uf)
                    if num:
                        calc = num * valor_uf_fijo
                        res = {"orig": f"{formato_chile(num)} UF", "dest": f"${formato_chile(calc, True)}", "ref": "UF Fija", "tipo": "MANUAL"}
                
                if res:
                    st.session_state.historial_ventana.append(res)
                    st.session_state.historial_acumulado.append(res)
                    st.rerun()

        if st.session_state.historial_ventana:
            actual = st.session_state.historial_ventana[-1]
            st.markdown("### 💎 Último Cálculo:")
            st.success(f"**{actual['orig']}** = **{actual['dest']}**")
            st.divider()
            for it in reversed(st.session_state.historial_ventana):
                st.code(f"{it['orig']} -> {it['dest']} | {it['ref']}")

elif opcion == "Buscar Fecha por Valor":
    st.title("🔍 Buscar Fecha según Valor UF")
    col1, col2 = st.columns(2)
    with col1: ini = st.text_input("Fecha Inicio:", placeholder="01-01-2024")
    with col2: fin = st.text_input("Fecha Término:", placeholder="31-12-2024")
    target_txt = st.text_input("Valor UF a buscar:")
    target_val = limpiar_monto(target_txt)
    if st.button("Iniciar Búsqueda") and target_val:
        try:
            start_date = datetime.strptime(ini, "%d-%m-%Y")
            end_date = datetime.strptime(fin, "%d-%m-%Y")
            uf_history = []
            total_days = (end_date - start_date).days + 1
            progress_bar = st.progress(0)
            for i in range(total_days):
                current = start_date + timedelta(days=i)
                f_str = current.strftime("%d-%m-%Y")
                try:
                    r = requests.get(f"https://mindicador.cl/api/uf/{f_str}", timeout=5).json()
                    if r['serie']: uf_history.append({'date': f_str, 'valor': r['serie'][0]['valor']})
                except: pass
                progress_bar.progress((i + 1) / total_days)
            if uf_history:
                exacts = [it['date'] for it in uf_history if abs(it['valor'] - target_val) < 0.01]
                if exacts:
                    for e in exacts: st.success(f"✅ Encontrado: {e}")
                else:
                    closest = min(uf_history, key=lambda x: abs(x['valor'] - target_val))
                    st.warning(f"Más cercano: {closest['date']} (${formato_chile(closest['valor'])})")
        except: st.error("Error en formato de fechas.")

elif opcion == "📜 Historial General":
    st.title("📜 Historial Acumulado Eterno")
    if st.button("🗑️ Borrar Historial Eterno"):
        st.session_state.historial_acumulado = []
        st.rerun()
    st.divider()
    if st.session_state.historial_acumulado:
        for item in reversed(st.session_state.historial_acumulado):
            st.code(f"[{item['tipo']}] {item['orig']} -> {item['dest']} | {item['ref']}")
    else:
        st.info("El historial está vacío.")
