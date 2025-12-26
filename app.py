import streamlit as st
import requests
from datetime import datetime, timedelta
st.set_page_config(page_title="Herramientas UF Pro", page_icon="📈", layout="centered")
if 'lista_negocios' not in st.session_state:
    st.session_state['lista_negocios'] = []
def formatear_chile(valor, es_clp=False):
    """Convierte 1234.56 a 1.234,56"""
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
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    ["UF Automática (Fecha)", "UF Manual (Valor fijo)", "Buscar Fecha por Valor"]
)
st.sidebar.divider()
if st.sidebar.button("🗑️ BORRAR TODO EL HISTORIAL"):
    st.session_state['lista_negocios'] = []
    st.rerun()
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
                    if st.form_submit_button("Convertir"):
                        monto_num = limpiar_monto(monto_input)
                        if monto_num:
                            res_uf = monto_num / valor_uf
                            st.session_state['lista_negocios'].append({
                                "tipo": "AUTO", "clp": monto_num, "uf": res_uf, "info": fecha_str
                            })
                            st.rerun()
            else: st.warning("No hay datos para esta fecha.")
        except ValueError: st.error("Formato DD-MM-AAAA incorrecto.")

elif opcion == "UF Manual (Valor fijo)":
    st.title("⚙️ UF Manual")
    uf_manual_txt = st.text_input("1. Valor UF base:", placeholder="33750.00")
    valor_uf_fijo = limpiar_monto(uf_manual_txt)
    
    if valor_uf_fijo:
        st.write(f"-> UF fijada: **${formatear_chile(valor_uf_fijo)}**")
        with st.form("form_manual", clear_on_submit=True):
            monto_input = st.text_input("2. Cantidad en CLP:")
            if st.form_submit_button("Convertir"):
                monto_num = limpiar_monto(monto_input)
                if monto_num:
                    res_uf = monto_num / valor_uf_fijo
                    st.session_state['lista_negocios'].append({
                        "tipo": "MANUAL", "clp": monto_num, "uf": res_uf, "info": f"UF: {formatear_chile(valor_uf_fijo)}"
                    })
                    st.rerun()

elif opcion == "Buscar Fecha por Valor":

    st.title("🔍 Buscar Fecha según Valor UF")
    col1, col2 = st.columns(2)
    with col1: ini = st.text_input("Fecha Inicio:", placeholder="01-01-2024")
    with col2: fin = st.text_input("Fecha Término:", placeholder="31-12-2024")
    val_buscar = st.text_input("Valor UF a buscar:")
    target = limpiar_monto(val_buscar)
    if st.button("Iniciar Búsqueda") and target:
        try:
            start = datetime.strptime(ini, "%d-%m-%Y")
            end = datetime.strptime(fin, "%d-%m-%Y")
            uf_history = []
            progress = st.progress(0)
            total = (end - start).days + 1
            for i in range(total):
                curr = (start + timedelta(days=i)).strftime("%d-%m-%Y")
                try:
                    r = requests.get(f"https://mindicador.cl/api/uf/{curr}", timeout=5).json()
                    if r['serie']: uf_history.append({'date': curr, 'valor': r['serie'][0]['valor']})
                except: pass
                progress.progress((i + 1) / total)
            if uf_history:
                exacts = [it['date'] for it in uf_history if abs(it['valor'] - target) < 0.01]
                if exacts:
                    for e in exacts: st.success(f"✅ Encontrado: {e}")
                else:
                    closest = min(uf_history, key=lambda x: abs(x['valor'] - target))
                    st.warning(f"Más cercano: {closest['date']} (${formatear_chile(closest['valor'])})")
        except: st.error("Error en fechas.")

if st.session_state['lista_negocios']:
    st.markdown("---")
    st.subheader("📜 Historial de Cálculos")
    
    ult = st.session_state['lista_negocios'][-1]
    st.write("✨ **Último resultado:**")
    c1, c2 = st.columns(2)
    
    c1.metric("Ingresado", f"${formatear_chile(ult['clp'], es_clp=True)}")
    c2.metric("Conversión", f"{formatear_chile(ult['uf'])} UF")
    
    with st.expander("Ver historial completo", expanded=True):
        for item in reversed(st.session_state['lista_negocios']):
            clp_f = formatear_chile(item['clp'], es_clp=True)
            uf_f = formatear_chile(item['uf'])
            st.code(f"[{item['tipo']}] ${clp_f} CLP -> {uf_f} UF ({item['info']})")
