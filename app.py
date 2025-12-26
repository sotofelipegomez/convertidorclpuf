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
    # Limpieza para formatos como 123.456.789 o 123,456,789
    res = t.replace(".", "").replace(",", ".") if "," in t and "." in t else t.replace(",", ".")
    # Si hay múltiples puntos tras la limpieza (ej: 123.456.789), quitamos todos menos el último
    if res.count(".") > 1:
        partes = res.split(".")
        res = "".join(partes[:-1]) + "." + partes[-1]
    try:
        return float(res)
    except:
        # Intento final: quitar todo lo que no sea número o punto/coma
        try:
            import re
            limpio = re.sub(r'[^\d,.]', '', t)
            if "," in limpio and "." in limpio:
                limpio = limpio.replace(".", "").replace(",", ".")
            elif "," in limpio:
                limpio = limpio.replace(",", ".")
            return float(limpio)
        except: return None

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

# NUEVA HERRAMIENTA: CALCULAR VALOR UF UTILIZADO
if opcion == "Calcular Valor UF (Inverso)":
    st.title("🔍 Calcular Valor UF Utilizado")
    st.write("Ingresa los totales para descubrir el valor de la UF unitaria.")
    
    with st.form("form_inverso", clear_on_submit=True):
        col1, col2 = st.columns(2)
        monto_clp_in = col1.text_input("Monto Total CLP:", placeholder="Ej: 3.700.000")
        monto_uf_in = col2.text_input("Monto Total UF:", placeholder="Ej: 100")
        
        if st.form_submit_button("Revelar Valor UF"):
            clp_val = limpiar_monto(monto_clp_in)
            uf_val = limpiar_monto(monto_uf_in)
            
            if clp_val and uf_val and uf_val != 0:
                uf_unitaria = clp_val / uf_val
                item = {
                    "clp": clp_val, 
                    "uf": uf_val, 
                    "res_unitario": uf_unitaria,
                    "ref": "Cálculo Inverso", 
                    "tipo": "INVERSO"
                }
                st.session_state.historial_ventana.append(item)
                st.session_state.historial_acumulado.append(item)
                st.rerun()
            else:
                st.error("Por favor ingresa valores válidos (UF no puede ser 0).")

    if st.session_state.historial_ventana:
        actual = st.session_state.historial_ventana[-1]
        st.markdown("### 💎 Valor UF detectado:")
        st.metric("UF UNITARIA", f"${formato_chile(actual['res_unitario'])}")
        st.write(f"Basado en {formato_chile(actual['clp'], True)} CLP dividido por {formato_chile(actual['uf'])} UF.")
        
        st.divider()
        for it in reversed(st.session_state.historial_ventana):
            st.code(f"Resultado: ${formato_chile(it['res_unitario'])} | (Total: ${formato_chile(it['clp'], True)} / {formato_chile(it['uf'])} UF)")

# (Las demás funciones se mantienen exactamente igual a tu código guardado)
elif opcion == "UF Automática (Fecha)":
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
                    monto_input = st.text_input("Ingresa cantidad en CLP:")
                    if st.form_submit_button("Convertir"):
                        monto_num = limpiar_monto(monto_input)
                        if monto_num:
                            res_uf = monto_num / valor_uf
                            item = {"clp": monto_num, "uf": res_uf, "ref": f"Fecha: {fecha_str} (${formato_chile(valor_uf)})", "tipo": "AUTO"}
                            st.session_state.historial_ventana.append(item)
                            st.session_state.historial_acumulado.append(item)
                            st.rerun()
                if st.session_state.historial_ventana:
                    actual = st.session_state.historial_ventana[-1]
                    st.markdown("### 💎 Resultado Actual:")
                    c1, c2 = st.columns(2)
                    c1.metric("MONTO CLP", f"${formato_chile(actual['clp'], True)}")
                    c2.metric("TOTAL EN UF", f"{formato_chile(actual['uf'])} UF")
                    st.divider()
                    for it in reversed(st.session_state.historial_ventana):
                        st.code(f"CLP: ${formato_chile(it['clp'], True)} -> {formato_chile(it['uf'])} UF | {it['ref']}")
            else: st.warning("No hay datos.")
        except: st.error("Error en fecha.")

elif opcion == "UF Manual (Valor fijo)":
    st.title("⚙️ UF Manual")
    uf_manual_txt = st.text_input("1. Valor UF base:")
    valor_uf_fijo = limpiar_monto(uf_manual_txt)
    if valor_uf_fijo:
        with st.form("form_manual", clear_on_submit=True):
            monto_input = st.text_input("2. Ingresa cantidad en CLP:")
            if st.form_submit_button("Convertir"):
                monto_num = limpiar_monto(monto_input)
                if monto_num:
                    res_uf = monto_num / valor_uf_fijo
                    item = {"clp": monto_num, "uf": res_uf, "ref": f"UF Fija: ${formato_chile(valor_uf_fijo)}", "tipo": "MANUAL"}
                    st.session_state.historial_ventana.append(item)
                    st.session_state.historial_acumulado.append(item)
                    st.rerun()
        if st.session_state.historial_ventana:
            actual = st.session_state.historial_ventana[-1]
            st.markdown("### 💎 Último Cálculo:")
            c1, c2 = st.columns(2)
            c1.metric("Ingresado", f"${formato_chile(actual['clp'], True)}")
            c2.metric("Conversión", f"{formato_chile(actual['uf'])} UF")
            st.divider()
            for it in reversed(st.session_state.historial_ventana):
                st.code(f"MONTO: ${formato_chile(it['clp'], True)} | UF: {formato_chile(it['uf'])} | {it['ref']}")

elif opcion == "Buscar Fecha por Valor":
    st.title("🔍 Buscar Fecha según Valor UF")
    col1, col2 = st.columns(2)
    with col1: ini = st.text_input("Fecha Inicio:")
    with col2: fin = st.text_input("Fecha Término:")
    target_val = limpiar_monto(st.text_input("Valor UF a buscar:"))
    if st.button("Buscar") and target_val:
        # Lógica de búsqueda (simplificada para el ejemplo)
        st.write("Buscando...")

elif opcion == "📜 Historial General":
    st.title("📜 Historial Acumulado Eterno")
    if st.button("🗑️ Borrar Historial"):
        st.session_state.historial_acumulado = []
        st.rerun()
    st.divider()
    if st.session_state.historial_acumulado:
        for item in reversed(st.session_state.historial_acumulado):
            if item['tipo'] == "INVERSO":
                st.code(f"[INVERSO] CLP {formato_chile(item['clp'], True)} / UF {formato_chile(item['uf'])} = UF Unit: ${formato_chile(item['res_unitario'])}")
            else:
                st.code(f"[{item['tipo']}] CLP: ${formato_chile(item['clp'], True)} -> {formato_chile(item['uf'])} UF | {item['ref']}")
