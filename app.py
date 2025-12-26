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
    
    # Ingreso manual de fecha
    fecha_txt = st.text_input("Ingresa la fecha (DD-MM-AAAA):", placeholder="Ej: 01-07-2022")
    
    if fecha_txt:
        try:
            # Validamos el formato ingresado
            fecha_valida = datetime.strptime(fecha_txt, "%d-%m-%Y")
            fecha_str = fecha_valida.strftime("%d-%m-%Y")
            
            url = f"https://mindicador.cl/api/uf/{fecha_str}"
            data = requests.get(url).json()
            valor_uf = data['serie'][0]['valor'] if data['serie'] else None
            
            if valor_uf:
                st.success(f"Valor UF para el {fecha_str}: **${valor_uf:,.2f}**")
                monto_input = st.text_input("Monto en CLP para convertir:")
                monto_num = limpiar_monto(monto_input)
                if monto_num:
                    res = monto_num / valor_uf
                    st.metric("Resultado", f"{res:,.2f} UF")
            else:
                st.warning("No hay datos para esa fecha específica.")
        except ValueError:
            st.error("Formato de fecha incorrecto. Usa DD-MM-AAAA (ej: 01-07-2022)")

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
        inicio_txt = st.text_input("Fecha Inicio (DD-MM-AAAA):", placeholder="01-01-2024")
    with col2:
        fin_txt = st.text_input("Fecha Término (DD-MM-AAAA):", placeholder="31-01-2024")

    target_txt = st.text_input("Valor UF que buscas (Ej: 36000.50):")
    target_val = limpiar_monto(target_txt)

    if st.button("Iniciar Búsqueda"):
        try:
            start_date = datetime.strptime(inicio_txt, "%d-%m-%Y")
            end_date = datetime.strptime(fin_txt, "%d-%m-%Y")
            
            if not target_val:
                st.error("Ingresa un valor de UF válido.")
            elif start_date > end_date:
                st.error("La fecha de inicio debe ser anterior a la de término.")
            else:
                uf_history = []
                total_days = (end_date - start_date).days + 1
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(total_days):
                    current = start_date + timedelta(days=i)
                    f_str = current.strftime("%d-%m-%Y")
                    status_text.text(f"Consultando: {f_str}")
                    try:
                        r = requests.get(f"https://mindicador.cl/api/uf/{f_str}", timeout=5)
                        d = r.json()
                        if d['serie']:
                            val = float(d['serie'][0]['valor'])
                            uf_history.append({'date': f_str, 'valor': val})
                    except: pass
                    progress_bar.progress((i + 1) / total_days)
                
                status_text.empty()
                progress_bar.empty()

                if uf_history:
                    tolerance = 0.01
                    exacts = [item['date'] for item in uf_history if abs(item['valor'] - target_val) < tolerance]
                    if exacts:
                        st.success(f"¡Encontrado! El valor ${target_val:,.2f} coincide con:")
                        for e in exacts: st.write(f"✅ {e}")
                    else:
                        closest = min(uf_history, key=lambda x: abs(x['valor'] - target_val))
                        st.warning(f"No hay coincidencia exacta. El más cercano: {closest['date']} (${closest['valor']:,.2f})")
        except ValueError:
            st.error("Asegúrate de que ambas fechas tengan el formato DD-MM-AAAA")
