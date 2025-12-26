import streamlit as st
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE LA WEB ---
st.set_page_config(page_title="Mi Panel de UF", page_icon="📈")

# --- FUNCIÓN COMPARTIDA (Tu lógica de limpieza robusta) ---
def limpiar_monto_clp(texto):
    if not texto.strip():
        return None
    
    monto_input_processed = texto.strip()
    clp_limpio = monto_input_processed
    last_comma_idx = monto_input_processed.rfind(',')
    last_dot_idx = monto_input_processed.rfind('.')

    if last_comma_idx != -1 and last_dot_idx != -1:
        if last_comma_idx > last_dot_idx:
            clp_limpio = monto_input_processed.replace(".", "").replace(",", ".")
        else:
            clp_limpio = monto_input_processed.replace(",", "")
    elif last_comma_idx != -1:
        parts = monto_input_processed.split(',')
        if len(parts[-1]) == 2 and len(parts) > 1:
             clp_limpio = monto_input_processed.replace(",", ".")
        else:
            clp_limpio = monto_input_processed.replace(",", "")
    elif last_dot_idx != -1:
        parts = monto_input_processed.split('.')
        if len(parts[-1]) == 2 and len(parts) > 1:
             clp_limpio = monto_input_processed
        else:
            clp_limpio = monto_input_processed.replace(".", "")
    
    try:
        return float(clp_limpio)
    except:
        return None

# --- MENÚ DE OPCIONES (BARRA LATERAL) ---
st.sidebar.title("Menú de Herramientas")
opcion = st.sidebar.radio(
    "Selecciona qué quieres hacer:",
    ("UF Automática (por fecha)", "UF Manual (valor fijo)")
)

st.sidebar.divider()
st.sidebar.caption("Solo para uso personal")

# --- OPCIÓN 1: UF AUTOMÁTICA ---
if opcion == "UF Automática (por fecha)":
    st.title("💰 UF Automática (API)")
    st.info("Esta opción busca el valor oficial de la UF en una fecha específica.")

    fecha_sel = st.date_input("1. Selecciona la fecha:", value=datetime.now())
    fecha_url = fecha_sel.strftime("%d-%m-%Y")

    # Obtener valor de la API
    url = f"https://mindicador.cl/api/uf/{fecha_url}"
    try:
        data = requests.get(url).json()
        if data['serie']:
            valor_uf = data['serie'][0]['valor']
            st.success(f"Valor UF detectado: **${valor_uf:,.2f}**")
            
            monto_input = st.text_input("2. Ingresa monto en CLP para convertir:")
            monto_final = limpiar_monto_clp(monto_input)
            
            if monto_final:
                resultado_uf = monto_final / valor_uf
                st.metric("Resultado", f"{resultado_uf:,.2f} UF")
        else:
            st.warning("No hay datos para esta fecha.")
    except:
        st.error("Error al conectar con la API.")

# --- OPCIÓN 2: UF MANUAL ---
elif opcion == "UF Manual (valor fijo)":
    st.title("⚙️ UF con Valor Manual")
    st.info("Usa esta opción si ya conoces el valor de la UF o quieres usar uno ficticio.")

    uf_manual_raw = st.text_input("1. Ingresa el valor de la UF que quieres usar:", placeholder="Ej: 37123.45")
    valor_uf_fijo = limpiar_monto_clp(uf_manual_raw)

    if valor_uf_fijo:
        st.write(f"Sincronizado con UF a: **${valor_uf_fijo:,.2f}**")
        
        monto_input = st.text_input("2. Ingresa monto en CLP para convertir:")
        monto_final = limpiar_monto_clp(monto_input)
        
        if monto_final:
            resultado_uf = monto_final / valor_uf_fijo
            st.metric("Resultado", f"{resultado_uf:,.2f} UF")
