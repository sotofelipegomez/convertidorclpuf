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
    t = texto.strip().replace("$", "").replace(" ", "")
    
    if "." in t and "," in t:
        if t.rfind(".") > t.rfind(","): 
            t = t.replace(",", "")
        else: 
            t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        if t.count(",") > 1 or len(t.split(",")[-1]) != 2:
            t = t.replace(",", "")
        else:
            t = t.replace(",", ".")
    elif "." in t:
        if t.count(".") > 1 or len(t.split(".")[-1]) != 2:
            t = t.replace(".", "")
            
    try:
        return float(t)
    except:
        return None

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

if opcion == "UF Automática (Fecha)":
    st.title("💰 UF Automática por Fecha")
    
    # Formulario unificado para evitar el error de "Fecha inválida"
    with st.form("form_auto_completo", clear_on_submit=False):
        fecha_input = st.text_input("Ingresa la fecha (DD-MM-AAAA):", placeholder="Ej: 01-07-2022")
        monto_input = st.text_input("Ingresa cantidad en CLP:", placeholder="Ej: 123.123.123")
        enviar = st.form_submit_button("Convertir")
        
        if enviar:
            if not fecha_input or not monto_input:
                st.error("Por favor, completa ambos campos.")
            else:
                try:
                    fecha_valida = datetime.strptime(fecha_input, "%d-%m-%Y")
                    f_str = fecha_valida.strftime("%d-%m-%Y")
                    
                    # Petición a la API
                    url = f"https://mindicador.cl/api/uf/{f_str}"
                    data = requests.get(url).json()
                    
                    if data['serie']:
                        v_uf = data['serie'][0]['valor']
                        monto_num = limpiar_monto(monto_input)
                        
                        if monto_num:
                            res_uf = monto_num / v_uf
                            item = {
                                "clp": monto_num, 
                                "uf": res_uf, 
                                "ref": f"Fecha: {f_str} (${formato_chile(v_uf)})", 
                                "tipo": "AUTO"
                            }
                            st.session_state.historial_ventana.append(item)
                            st.session_state.historial_acumulado.append(item)
                            st.success(f"Valor UF al {f_str}: ${formato_chile(v_uf)}")
                        else:
                            st.error("Monto CLP no válido.")
                    else:
                        st.warning("No hay datos de UF para esa fecha.")
                except ValueError:
                    st.error("Formato de fecha incorrecto (usa DD-MM-AAAA).")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

    # Mostrar resultados debajo del formulario
    if st.session_state.historial_ventana:
        act = st.session_state.historial_ventana[-1]
        st.markdown("### 💎 Resultado Actual:")
        c1, c2 = st.columns(2)
        c1.metric("MONTO CLP", f"${formato_chile(act['clp'], True)}")
        c2.metric("TOTAL EN UF", f"{formato_chile(act['uf'])} UF")
        st.divider()
        for it in reversed(st.session_state.historial_ventana):
            st.code(f"CLP: ${formato_chile(it['clp'], True)} -> {formato_chile(it['uf'])} UF | {it['ref']}")

elif opcion == "UF Manual (Valor fijo)":
    st.title("⚙️ UF Manual")
    v_uf_txt = st.text_input("1. Valor UF base:", placeholder="35.000")
    v_fijo = limpiar_monto(v_uf_txt)
    if v_fijo:
        with st.form("form_manual", clear_on_submit=True):
            monto_in = st.text_input("2. Cantidad en CLP:")
            if st.form_submit_button("Convertir"):
                num = limpiar_monto(monto_in)
                if num:
                    res = num / v_fijo
                    item = {"clp": num, "uf": res, "ref": f"UF Fija: ${formato_chile(v_fijo)}", "tipo": "MANUAL"}
                    st.session_state.historial_ventana.append(item)
                    st.session_state.historial_acumulado.append(item)
                    st.rerun()
        if st.session_state.historial_ventana:
            act = st.session_state.historial_ventana[-1]
            st.markdown("### 💎 Último Cálculo:")
            c1, c2 = st.columns(2)
            c1.metric("Ingresado", f"${formato_chile(act['clp'], True)}")
            c2.metric("Conversión", f"{formato_chile(act['uf'])} UF")
            st.divider()
            for it in reversed(st.session_state.historial_ventana):
                st.code(f"MONTO: ${formato_chile(it['clp'], True)} | UF: {formato_chile(it['uf'])} | {it['ref']}")

elif opcion == "Calcular Valor UF (Inverso)":
    st.title("🔍 Calcular Valor UF Utilizado")
    with st.form("form_inverso", clear_on_submit=True):
        col1, col2 = st.columns(2)
        monto_clp_in = col1.text_input("Monto Total CLP:", placeholder="Ej: 123.456.789")
        monto_uf_in = col2.text_input("Monto Total UF:", placeholder="Ej: 3.450,12")
        if st.form_submit_button("Revelar Valor UF"):
            clp_val = limpiar_monto(monto_clp_in)
            uf_val = limpiar_monto(monto_uf_in)
            if clp_val and uf_val and uf_val != 0:
                uf_unitaria = clp_val / uf_val
                item = {"clp": clp_val, "uf": uf_val, "res_unitario": uf_unitaria, "ref": "Cálculo Inverso", "tipo": "INVERSO"}
                st.session_state.historial_ventana.append(item)
                st.session_state.historial_acumulado.append(item)
                st.rerun()

    if st.session_state.historial_ventana:
        actual = st.session_state.historial_ventana[-1]
        st.markdown("### 💎 Valor UF detectado:")
        st.metric("UF UNITARIA", f"${formato_chile(actual['res_unitario'])}")
        st.divider()
        for it in reversed(st.session_state.historial_ventana):
            st.code(f"Resultado: ${formato_chile(it['res_unitario'])} | (Total: ${formato_chile(it['clp'], True)} / {formato_chile(it['uf'])} UF)")

elif opcion == "Buscar Fecha por Valor":
    st.title("🔍 Buscar Fecha según Valor UF")
    st.write("Módulo de búsqueda avanzada.")

elif opcion == "📜 Historial General":
    st.title("📜 Historial Acumulado Eterno")
    if st.button("🗑️ Borrar Historial"):
        st.session_state.historial_acumulado = []
        st.rerun()
    st.divider()
    if st.session_state.historial_acumulado:
        for item in reversed(st.session_state.historial_acumulado):
            if item['tipo'] == "INVERSO":
                st.code(f"[INVERSO] {formato_chile(item['clp'], True)} CLP / {formato_chile(item['uf'])} UF = UF: ${formato_chile(item['res_unitario'])}")
            else:
                st.code(f"[{item['tipo']}] CLP: ${formato_chile(item['clp'], True)} -> {formato_chile(item['uf'])} UF | {item['ref']}")
