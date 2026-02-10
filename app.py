import streamlit as st
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Remarcador de Precios",
    page_icon="💰",
    layout="wide"
)

# --- LÓGICA DE NEGOCIO (TU TABLA MAESTRA) ---
def calcular_markup(precio_original):
    p = float(precio_original)
    
    if p < 10:
        return p + 0.50
    elif 10 <= p < 30:
        return p + 2.00
    elif 30 <= p < 100:
        return p + 5.00
    elif 100 <= p < 200:
        return p + 7.50
    elif 200 <= p < 400:
        return p + 15.00 if p < 300 else p + 20.00
    elif 400 <= p < 500:
        return p + 25.00
    elif 500 <= p < 800:
        return p + 30.00 if p < 600 else p + 40.00
    elif 800 <= p < 900:
        return p + 45.00
    elif p >= 900:
        return p + 50.00
    else:
        return p

def procesar_whatsapp(texto):
    lineas = texto.splitlines()
    resultado = []
    
    for linea in lineas:
        # Busca precios con formato: *$500*, $500, $500.00
        match = re.search(r'(\*\$|\$)([\d\.,]+)(\*?)', linea)
        
        if match:
            try:
                precio_str = match.group(2).replace(',', '')
                precio_base = float(precio_str)
                precio_nuevo = calcular_markup(precio_base)
                
                # Formato sin decimales si es entero
                if precio_nuevo.is_integer():
                    precio_final_str = f"{int(precio_nuevo)}"
                else:
                    precio_final_str = f"{precio_nuevo:.2f}"
                
                bloque_original = match.group(0)
                bloque_nuevo = f"{match.group(1)}{precio_final_str}{match.group(3)}"
                
                linea_nueva = linea.replace(bloque_original, bloque_nuevo)
                resultado.append(linea_nueva)
            except:
                resultado.append(linea)
        else:
            resultado.append(linea)

    return "\n".join(resultado)

# --- INTERFAZ DE USUARIO (STREAMLIT) ---

st.title("📈 Traductor de Precios Mayorista -> Cliente")
st.markdown("""
Esta herramienta toma la lista de WhatsApp de tu proveedor y aplica automáticamente 
la **escala de aumentos** definida.
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Pega la lista del Proveedor")
    input_text = st.text_area("Lista con precios de costo (WhatsApp)", height=400, placeholder="Pega aquí el mensaje tal cual te llegó...")

with col2:
    st.subheader("2. Lista Lista para enviar")
    if input_text:
        output_text = procesar_whatsapp(input_text)
        st.text_area("Lista con precios de venta (Resultado)", value=output_text, height=400)
        st.info("👆 Copia el texto de arriba y pégalo en el chat de tus clientes.")
    else:
        st.warning("Esperando texto...")

# --- BARRA LATERAL (REFERENCIA) ---
with st.sidebar:
    st.header("Reglas Aplicadas")
    st.write("• **$1-$9**: +$0.50")
    st.write("• **$10-$29**: +$2.00")
    st.write("• **$30-$99**: +$5.00")
    st.write("• **$100-$199**: +$7.50")
    st.write("• **$200-$399**: +$15 o +$20")
    st.write("• **$400-$499**: +$25")
    st.write("• **$500-$799**: +$30 o +$40")
    st.write("• **$800-$899**: +$45")
    st.write("• **+$900**: +$50")
