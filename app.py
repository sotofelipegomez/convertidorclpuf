import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Herramientas UF Pro", page_icon="📈")

# --- FUNCIÓN DE LIMPIEZA ROBUSTA ---
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

# --- GESTIÓN DE HISTORIAL (Se limpia al cambiar de página) ---
if 'last_opcion' not in st.session_state:
    st.session_state.last_opcion = ""
    st.session_state.historial = []

# MENÚ LATERAL
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    ["UF Automática (Fecha)", "UF Manual (Valor fijo)", "Buscar Fecha por Valor"]
)

# Si el usuario cambia de pestaña, limpiamos el historial
if st.session_state.last_opcion != opcion:
    st.session_state.historial = []
    st.session_state.last_opcion = opcion

# --- INTERFAZ ---

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
                st.info(f"Valor UF detectado: **${valor_uf:,.2f}**")
                
                # Input de montos
                with st.form("form_auto", clear_on_submit=True):
                    monto_input = st.text_input("Ingresa cantidad en CLP:")
                    enviar = st.form_submit_button("Convertir")
                    
                    if enviar and monto_input:
                        monto_num = limpiar_monto(monto_input)
                        if monto_num:
                            res_uf = monto_num / valor_uf
                            # Guardar en historial
                            st.session_state.historial.append({
                                "clp": monto_num,
                                "uf": res_uf
                            })
                
                # Mostrar historial estilo consola
                for item in reversed(st.session_state.historial):
                    st.code(f"""
=============================================
MONTO INGRESADO: ${item['clp']:,.2f} CLP
EQUIVALENCIA EN UF: {item['uf']:,.2f} UF
=============================================""")

            else: st.warning("No hay datos para esa fecha.")
        except ValueError: st.error("Formato DD-MM-AAAA incorrecto.")

elif opcion == "UF Manual (Valor fijo)":
    st.title("⚙️ UF Manual")
    uf_manual_txt = st.text_input("1. Ingresa el valor de la UF base:", placeholder="33750.00")
    valor_uf_fijo = limpiar_monto(uf_manual_txt)
    
    if valor_uf_fijo:
        st.write(f"-> Valor UF fijado para esta sesión: **${valor_uf_fijo:,.2f}**")
        
        with st.form("form_manual", clear_on_submit=True):
            monto_input = st.text_input("2. Ingresa cantidad en CLP:")
            enviar = st.form_submit_button("Convertir")
            
            if enviar and monto_input:
                monto_num = limpiar_monto(monto_input)
                if monto_num:
                    res_uf = monto_num / valor_uf_fijo
                    st.session_state.historial.append({"clp": monto_num, "uf": res_uf})

        for item in reversed(st.session_state.historial):
            st.code(f"""
=============================================
MONTO INGRESADO: ${item['clp']:,.2f} CLP
EQUIVALENCIA EN UF: {item['uf']:,.2f} UF
=============================================""")

elif opcion == "Buscar Fecha por Valor":
    st.title("🔍 Buscar Fecha según Valor UF")
    col1, col2 = st.columns(2)
    with col1: inicio_txt = st.text_input("Fecha Inicio:", placeholder="01-01-2024")
    with col2: fin_txt = st.text_input("Fecha Término:", placeholder="31-01-2024")
    target_txt = st.text_input("Valor UF a buscar:")
    target_val = limpiar_monto(target_txt)

    if st.button("Iniciar Búsqueda") and target_val:
        try:
            start_date = datetime.strptime(inicio_txt, "%d-%m-%Y")
            end_date = datetime.strptime(fin_txt, "%d-%m-%Y")
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
                tolerance = 0.01
                exacts = [it['date'] for it in uf_history if abs(it['valor'] - target_val) < tolerance]
                if exacts:
                    for e in exacts: st.success(f"✅ Encontrado: {e}")
                else:
                    closest = min(uf_history, key=lambda x: abs(x['valor'] - target_val))
                    st.warning(f"No exacto. Más cercano: {closest['date']} (${closest['valor']:,.2f})")
        except: st.error("Revisa el formato de fechas (DD-MM-AAAA)")
