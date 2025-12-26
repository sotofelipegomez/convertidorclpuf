import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Herramientas UF Pro", page_icon="📈")

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

# MENÚ LATERAL
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una herramienta:",
    ["UF Automática (Fecha)", "UF Manual (Valor fijo)", "Buscar Fecha por Valor"]
)

if opcion == "UF Automática (Fecha)":
    st.title("💰 UF Automática por Fecha")
    fecha_sel = st.date_input("Selecciona la fecha:", value=datetime.now())
    fecha_str = fecha_sel.strftime("%d-%m-%Y")
    url = f"https://mindicador.cl/api/uf/{fecha_str}"
    try:
        data = requests.get(url).json()
        valor_uf = data['serie'][0]['valor'] if data['serie'] else None
        if valor_uf:
            st.success(f"Valor UF: **${valor_uf:,.2f}**")
            monto_txt = st.text_input("Monto en CLP:")
            monto_num = limpiar_monto(monto_txt)
            if monto_num:
                res = monto_num / valor_uf
                st.metric("Resultado", f"{res:,.2f} UF")
        else: st.warning("No hay datos para esta fecha.")
    except: st.error("Error de conexión.")

elif opcion == "UF Manual (Valor fijo)":
    st.title("⚙️ UF Manual")
    uf_manual_txt = st.text_input("Valor de la UF a usar:", placeholder="Ej: 37500.50")
    valor_uf_fijo = limpiar_monto(uf_manual_txt)
    if valor_uf_fijo:
        st.info(f"Usando UF: **${valor_uf_fijo:,.2f}**")
        monto_txt = st.text_input("Monto en CLP:")
        monto_num = limpiar_monto(monto_txt)
        if monto_num:
            res = monto_num / valor_uf_fijo
            st.metric("Resultado", f"{res:,.2f} UF")

elif opcion == "Buscar Fecha por Valor":
    st.title("🔍 Buscar Fecha según Valor UF")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha Inicio", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("Fecha Término", datetime.now())
    target_txt = st.text_input("Valor UF que buscas (Ej: 36000.50):")
    target_val = limpiar_monto(target_txt)
    if st.button("Iniciar Búsqueda") and target_val:
        if start_date > end_date:
            st.error("La fecha de inicio debe ser anterior a la de término.")
        else:
            uf_history = []
            current = start_date
            total_days = (end_date - start_date).days + 1
            progress_bar = st.progress(0)
            status_text = st.empty()
            day_count = 0
            while current <= end_date:
                f_str = current.strftime("%d-%m-%Y")
                status_text.text(f"Consultando: {f_str}")
                try:
                    r = requests.get(f"https://mindicador.cl/api/uf/{f_str}", timeout=5)
                    d = r.json()
                    if d['serie']:
                        val = float(d['serie'][0]['valor'])
                        uf_history.append({'date': f_str, 'valor': val})
                except: pass
                current += timedelta(days=1)
                day_count += 1
                progress_bar.progress(day_count / total_days)
            status_text.empty()
            progress_bar.empty()
            if uf_history:
                tolerance = 0.01
                exacts = [i['date'] for i in uf_history if abs(i['valor'] - target_val) < tolerance]
                if exacts:
                    st.success(f"¡Encontrado! El valor ${target_val:,.2f} coincide con:")
                    for e in exacts: st.write(f"✅ {e}")
                else:
                    st.warning(f"No hay coincidencia exacta para ${target_val:,.2f}.")
                    closest = min(uf_history, key=lambda x: abs(x['valor'] - target_val))
                    st.info(f"El día más cercano fue el **{closest['date']}** con un valor de **${closest['valor']:,.2f}**")
