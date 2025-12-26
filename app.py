import streamlit as st
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Conversor CLP a UF", page_icon="🇨🇱")

# Título e instrucciones
st.title("💰 Conversor Inteligente CLP a UF")
st.markdown("Extrae el valor de la UF automáticamente y convierte montos de forma robusta.")

# --- 1. SELECCIÓN DE FECHA ---
# Usamos un widget de calendario en lugar de input de texto
fecha_sel = st.date_input("Selecciona la fecha para el valor UF:", value=datetime.now())
fecha_url = fecha_sel.strftime("%d-%m-%Y")

# --- 2. OBTENER VALOR UF (Lógica de tu Colab) ---
@st.cache_data(ttl=3600) # Esto guarda el valor por 1 hora para que la web sea rápida
def obtener_valor_uf(fecha_str):
    try:
        url = f"https://mindicador.cl/api/uf/{fecha_str}"
        response = requests.get(url)
        data = response.json()
        if data['serie']:
            return data['serie'][0]['valor']
        return None
    except:
        return None

valor_uf_fecha = obtener_valor_uf(fecha_url)

if valor_uf_fecha:
    st.info(f"✅ Valor UF detectado para el {fecha_url}: **${valor_uf_fecha:,.2f}**")
    
    # --- 3. ENTRADA DE MONTO ---
    monto_input = st.text_input("Ingresa la cantidad en CLP (Ej: 132.132.122 o 132,132,122.48):", placeholder="0")

    if monto_input:
        # Tu lógica de LIMPIEZA Y PARSEO ROBUSTO (Mantenida igual)
        monto_input_processed = monto_input.strip()
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
            monto_clp = float(clp_limpio)
            monto_uf = monto_clp / valor_uf_fecha
            
            # Formateo para mostrar en pantalla
            uf_final = "{:,.2f}".format(monto_uf).replace(",", "X").replace(".", ",").replace("X", ".")
            clp_bonito = "{:,.0f}".format(monto_clp).replace(",", ".")

            # --- RESULTADO VISUAL ---
            st.divider()
            col1, col2 = st.columns(2)
            col1.metric("Monto CLP", f"${clp_bonito}")
            col2.metric("Equivalencia UF", f"{uf_final} UF")
            st.divider()

        except ValueError:
            st.error("❌ Error: No pudimos reconocer el monto. Revisa el formato.")
else:
    st.error(f"No se encontraron datos de UF para la fecha {fecha_url}.")

# Pie de página
st.caption("Solo tú tienes acceso a esta herramienta privada.")