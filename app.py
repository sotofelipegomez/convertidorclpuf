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
            res = t if len(parts[-1]) == 2 and len(parts) > 1 else t.replace(",", "")
        else:
            res = t
        return float(res)
    except: return None

# --- 5. MENÚ LATERAL (Con las 2 nuevas pestañas) ---
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    [
        "CLP a UF (Automático)", 
        "UF a CLP (Automático)", 
        "CLP a UF (Manual)", 
        "UF a CLP (Manual)", 
        "Buscar Fecha por Valor", 
        "📜 Historial General"
    ]
)

# Limpiar historial de ventana si cambia de pestaña
if st.session_state.last_opcion != opcion:
    st.session_state.historial_ventana = []
    st.session_state.last_opcion = opcion

# --- 6. LÓGICA DE HERRAMIENTAS ---

# --- BLOQUE AUTOMÁTICO ---
if "Automático" in opcion:
    st.title(f"💰 {opcion}")
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
                label_input = "Ingresa cantidad en CLP:" if "CLP a UF" in opcion else "Ingresa cantidad en UF:"
                
                with st.form("form_auto", clear_on_submit=True):
                    monto_in = st.text_input(label_input)
                    if st.form_submit_button("Convertir"):
                        num = limpiar_monto(monto_in)
                        if num:
                            if "CLP a UF" in opcion:
                                calc = num / v_uf
                                item = {"orig": f"${formato_chile(num, True)}", "dest": f"{formato_chile(calc)} UF", "ref": f"Fecha: {f_str} (${formato_chile(v_uf)})", "tipo": "AUTO"}
                            else:
                                calc = num * v_uf
                                item = {"orig": f"{formato_chile(num)} UF", "dest": f"${formato_chile(calc, True)}", "ref": f"Fecha: {f_str} (${formato_chile(v_uf)})", "tipo": "AUTO"}
                            
                            st.session_state.historial_ventana.append(item)
                            st.session_state.historial_acumulado.append(item)
                            st.rerun()

                if st.session_state.historial_ventana:
                    act = st.session_state.historial_ventana[-1]
                    st.markdown("### 💎 Resultado Actual:")
                    c1, c2 = st.columns(2)
                    c1.metric("INGRESADO", act['orig'])
                    c2.metric("CONVERSIÓN", act['dest'])
                    st.caption(f"📌 Calculado con {act['ref']}")
                    st.divider()
                    for it in reversed(st.session_state.historial_ventana):
                        st.code(f"{it['orig']} -> {it['dest']} | {it['ref']}")
            else: st.warning("No hay datos para esta fecha.")
        except: st.error("Formato de fecha incorrecto.")

# --- BLOQUE MANUAL ---
elif "Manual" in opcion:
    st.title(f"⚙️ {opcion}")
    v_uf_txt = st.text_input("1. Valor UF base:", placeholder="33750.00")
    v_uf_fijo = limpiar_monto(v_uf_txt)
    
    if v_uf_fijo:
        st.write(f"-> UF fijada: **${formato_chile(v_uf_fijo)}**")
        label_input = "2. Ingresa cantidad en CLP:" if "CLP a UF" in opcion else "2. Ingresa cantidad en UF:"
        
        with st.form("form_manual", clear_on_submit=True):
            monto_in = st.text_input(label_input)
            if st.form_submit_button("Convertir"):
                num = limpiar_monto(monto_in)
                if num:
                    if "CLP a UF" in opcion:
                        calc = num / v_uf_fijo
                        item = {"orig": f"${formato_chile(num, True)}", "dest": f"{formato_chile(calc)} UF", "ref": f"UF Fija: ${formato_chile(v_uf_fijo)}", "tipo": "MANUAL"}
                    else:
                        calc = num * v_uf_fijo
                        item = {"orig": f"{formato_chile(num)} UF", "dest": f"${formato_chile(calc, True)}", "ref": f"UF Fija: ${formato_chile(v_uf_fijo)}", "tipo": "MANUAL"}
                    
                    st.session_state.historial_ventana.append(item)
                    st.session_state.historial_acumulado.append(item)
                    st.rerun()

        if st.session_state.historial_ventana:
            act = st.session_state.historial_ventana[-1]
            st.markdown("### 💎 Último Cálculo:")
            c1, c2 = st.columns(2)
            c1.metric("INGRESADO", act['orig'])
            c2.metric("CONVERSIÓN", act['dest'])
            st.caption(f"📌 Calculado con {act['ref']}")
            st.divider()
            for it in reversed(st.session_state.historial_ventana):
                st.code(f"{it['orig']} -> {it['dest']} | {it['ref']}")

# --- OTRAS PÁGINAS ---
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
            progress_bar = st.progress(0)
            total_days = (end_date - start_date).days + 1
            for i in range(total_days):
                curr = (start_date + timedelta(days=i)).strftime("%d-%m-%Y")
                try:
                    r = requests.get(f"https://mindicador.cl/api/uf/{curr}", timeout=5).json()
                    if r['serie']: uf_history.append({'date': curr, 'valor': r['serie'][0]['valor']})
                except: pass
                progress_bar.progress((i + 1) / total_days)
            if uf_history:
                exacts = [it['date'] for it in uf_history if abs(it['valor'] - target_val) < 0.01]
                if exacts:
                    for e in exacts: st.success(f"✅ Encontrado: {e}")
                else:
                    closest = min(uf_history, key=lambda x: abs(x['valor'] - target_val))
                    st.warning(f"Más cercano: {closest['date']} (${formato_chile(closest['valor'])})")
        except: st.error("Error en fechas.")

elif opcion == "📜 Historial General":
    st.title("📜 Historial Acumulado Eterno")
    if st.button("🗑️ Borrar Historial Eterno"):
        st.session_state.historial_acumulado = []
        st.rerun()
    st.divider()
    if st.session_state.historial_acumulado:
        for item in reversed(st.session_state.historial_acumulado):
            st.code(f"[{item['tipo']}] {item['orig']} -> {item['dest']} | {item['ref']}")
    else: st.info("El historial está vacío.")
