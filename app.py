import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Herramientas UF Pro", page_icon="📈")

# --- FUNCIÓN DE FORMATO CHILENO (Puntos para miles, coma para decimales) ---
def formatear_chile(valor, es_clp=False):
    if valor is None: return ""
    decimales = 0 if es_clp else 2
    # Formateamos con comas y puntos estándar, luego los trocamos
    txt = f"{valor:,.{decimales}f}"
    return txt.replace(",", "X").replace(".", ",").replace("X", ".")

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

# --- GESTIÓN DE SESIÓN PERSISTENTE ---
if 'historial' not in st.session_state:
    st.session_state.historial = []

# MENÚ LATERAL
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    ["UF Automática (Fecha)", "UF Manual (Valor fijo)", "Buscar Fecha por Valor"]
)

# --- LÓGICA DE PÁGINAS ---

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
                st.info(f"Valor UF detectado: **${formatear_chile(valor_uf)}**")
                
                with st.form("form_auto", clear_on_submit=True):
                    monto_input = st.text_input("Ingresa cantidad en CLP:")
                    enviar = st.form_submit_button("Convertir")
                    
                    if enviar and monto_input:
                        monto_num = limpiar_monto(monto_input)
                        if monto_num:
                            res_uf = monto_num / valor_uf
                            # Guardamos tipo y fecha para el historial mixto
                            st.session_state.historial.append({
                                "tipo": "AUTO", "clp": monto_num, "uf": res_uf, "extra": fecha_str
                            })
                            st.rerun()
                
                if st.session_state.historial:
                    actual = st.session_state.historial[-1]
                    st.subheader("Resultado Actual:")
                    col1, col2 = st.columns(2)
                    col1.metric("MONTO CLP", f"${formatear_chile(actual['clp'], True)}")
                    col2.metric("TOTAL EN UF", f"{formatear_chile(actual['uf'])} UF")
                    
                    if st.button("Limpiar todo el historial"):
                        st.session_state.historial = []
                        st.rerun()
                    
                    st.divider()
                    st.write("📜 Historial acumulado:")
                    for item in reversed(st.session_state.historial):
                        clp_f = formatear_chile(item['clp'], True)
                        uf_f = formatear_chile(item['uf'])
                        info = item.get('extra', 'Manual')
                        st.code(f"[{item['tipo']}] CLP: ${clp_f} -> {uf_f} UF ({info})")

            else: st.warning("No hay datos para esa fecha.")
        except ValueError: st.error("Formato DD-MM-AAAA incorrecto.")

elif opcion == "UF Manual (Valor fijo)":
    st.title("⚙️ UF Manual")
    uf_manual_txt = st.text_input("1. Ingresa el valor de la UF base:", placeholder="33750,00")
    valor_uf_fijo = limpiar_monto(uf_manual_txt)
    
    if valor_uf_fijo:
        st.write(f"-> Valor UF fijado: **${formatear_chile(valor_uf_fijo)}**")
        
        with st.form("form_manual", clear_on_submit=True):
            monto_input = st.text_input("2. Ingresa cantidad en CLP:")
            enviar = st.form_submit_button("Convertir")
            
            if enviar and monto_input:
                monto_num = limpiar_monto(monto_input)
                if monto_num:
                    res_uf = monto_num / valor_uf_fijo
                    st.session_state.historial.append({
                        "tipo": "MANUAL", "clp": monto_num, "uf": res_uf, "extra": f"Base: {formatear_chile(valor_uf_fijo)}"
                    })
                    st.rerun()

        if st.session_state.historial:
            actual = st.session_state.historial[-1]
            st.markdown("### 💎 Último Cálculo:")
            c1, c2 = st.columns(2)
            c1.metric("Ingresado", f"${formatear_chile(actual['clp'], True)}")
            c2.metric("Conversión", f"{formatear_chile(actual['uf'])} UF")
            
            if st.button("Borrar lista"):
                st.session_state.historial = []
                st.rerun()
            
            st.divider()
            for item in reversed(st.session_state.historial):
                clp_f = formatear_chile(item['clp'], True)
                uf_f = formatear_chile(item['uf'])
                st.code(f"[{item['tipo']}] MONTO: ${clp_f} | UF: {uf_f}")

elif opcion == "Buscar Fecha por Valor":
    st.title("🔍 Buscar Fecha según Valor UF")
    col1, col2 = st.columns(2)
    with col1: inicio_txt = st.text_input("Fecha Inicio:", placeholder="01-01-2024")
    with col2: fin_txt = st.text_input("Fecha Término:", placeholder="31-12-2024")
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
                    if r['serie']:
                        uf_history.append({'date': f_str, 'valor': r['serie'][0]['valor']})
                except: pass
                progress_bar.progress((i + 1) / total_days)
            
            if uf_history:
                exacts = [it['date'] for it in uf_history if abs(it['valor'] - target_val) < 0.01]
                if exacts:
                    st.success(f"Encontrado en {len(exacts)} fechas:")
                    for e in exacts: st.write(f"✅ {e}")
                else:
                    closest = min(uf_history, key=lambda x: abs(x['valor'] - target_val))
                    st.warning(f"Más cercano: {closest['date']} (${formatear_chile(closest['valor'])})")
        except: st.error("Error en formato de fechas.")
