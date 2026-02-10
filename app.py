import streamlit as st
import re
import math
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Remarcador Pro v5",
    page_icon="💎",
    layout="wide"
)

# --- LÓGICA DE NEGOCIO (TABLA MAESTRA) ---
def calcular_nuevo_precio(valor):
    try:
        # Limpieza básica: si viene como texto "$1,200.00", lo convertimos a float
        if isinstance(valor, str):
            # Quitar símbolos de moneda y separadores de miles
            limpio = valor.replace('$', '').replace(',', '').replace('USD', '').strip()
            p = float(limpio)
        else:
            p = float(valor)
    except:
        return valor # Si no es un número, devolvemos el valor original (ej: "Consultar")

    markup = 0
    
    # --- ESCALAS DEFINIDAS ---
    if p < 10:
        markup = 0.50
    elif 10 <= p < 30:
        markup = 2.00
    elif 30 <= p < 120:
        markup = 5.00
    elif 120 <= p < 150:
        markup = 10.00
    elif 150 <= p < 290: # Unificado 150-219 y 220-289
        markup = 15.00 
    elif 290 <= p < 355:
        markup = 20.00
    elif 355 <= p < 415:
        markup = 25.00
    elif 415 <= p < 510:
        markup = 30.00
    elif 510 <= p < 615:
        markup = 30.00 if p < 550 else 35.00
    elif 615 <= p < 800:
        markup = 40.00
    elif 800 <= p < 1000:
        markup = 50.00
    else:
        # > $1000: 5.5% redondeado a 5
        raw_markup = p * 0.055
        markup = round(raw_markup / 5) * 5

    return p + markup

def procesar_texto_whatsapp(texto):
    lineas = texto.splitlines()
    resultado = []
    
    for linea in lineas:
        match = re.search(r'(\*\$|\$)([\d\.,]+)(\*?)', linea)
        if match:
            try:
                precio_str = match.group(2).replace(',', '')
                precio_base = float(precio_str)
                precio_nuevo = calcular_nuevo_precio(precio_base)
                
                if precio_nuevo.is_integer():
                    precio_final_str = f"{int(precio_nuevo):,}"
                else:
                    precio_final_str = f"{precio_nuevo:,.2f}"
                
                bloque_original = match.group(0)
                bloque_nuevo = f"{match.group(1)}{precio_final_str}{match.group(3)}"
                linea_nueva = linea.replace(bloque_original, bloque_nuevo)
                resultado.append(linea_nueva)
            except:
                resultado.append(linea)
        else:
            resultado.append(linea)
    return "\n".join(resultado)

# --- INTERFAZ DE USUARIO ---

st.title("💎 Remarcador de Precios Mayorista")

# Creamos dos pestañas para separar las funcionalidades
tab1, tab2 = st.tabs(["📝 Texto WhatsApp", "📂 Archivo Excel"])

# --- MÓDULO 1: TEXTO WHATSAPP ---
with tab1:
    st.markdown("### Copia y pega tu lista de WhatsApp")
    col1, col2 = st.columns(2)
    
    with col1:
        input_text = st.text_area("⬇️ Entrada (Precios Costo)", height=500, placeholder="Pega aquí...")
    
    with col2:
        if input_text:
            output_text = procesar_texto_whatsapp(input_text)
            st.text_area("✅ Salida (Precios Venta)", value=output_text, height=500)
            st.success("¡Texto procesado!")
        else:
            st.info("Esperando texto...")

# --- MÓDULO 2: ARCHIVO EXCEL ---
with tab2:
    st.markdown("### Sube tu Google Sheet (descárgalo como .xlsx)")
    
    uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx", "xls", "csv"])
    
    if uploaded_file:
        try:
            # Leer el archivo según extensión
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.write("Vista previa de tus datos:")
            st.dataframe(df.head(3))
            
            # Selector de columna
            columnas = df.columns.tolist()
            col_precio = st.selectbox("¿Cuál es la columna que tiene el PRECIO?", columnas)
            
            if st.button("🚀 Calcular Nuevos Precios"):
                # Crear nueva columna
                nombre_nueva_col = f"{col_precio} (Venta)"
                
                # Aplicar la función a cada fila
                df[nombre_nueva_col] = df[col_precio].apply(calcular_nuevo_precio)
                
                st.success("¡Cálculo terminado!")
                st.write("Vista previa del resultado:")
                st.dataframe(df[[col_precio, nombre_nueva_col]].head())
                
                # Convertir DF a Excel para descargar
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                datos_excel = output.getvalue()
                
                st.download_button(
                    label="📥 Descargar Excel con Precios Nuevos",
                    data=datos_excel,
                    file_name="lista_precios_venta.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
        except Exception as e:
            st.error(f"Hubo un error al leer el archivo: {e}")

# --- BARRA LATERAL (REFERENCIA) ---
with st.sidebar:
    st.header("📊 Tabla de Aumentos")
    st.markdown("---")
    st.write("• **$1 - $9**: +$0.50")
    st.write("• **$10 - $29**: +$2.00")
    st.write("• **$30 - $119**: +$5.00")
    st.write("• **$120 - $149**: +$10.00")
    st.write("• **$150 - $289**: +$15.00")
    st.write("• **$290 - $354**: +$20.00")
    st.write("• **$355 - $414**: +$25.00")
    st.write("• **$415 - $509**: +$30.00")
    st.markdown("---")
    st.write("• **$510 - $614**: +$30/$35")
    st.write("• **$615 - $799**: +$40.00")
    st.write("• **$800 - $999**: +$50.00")
    st.write("• **+$1,000**: +5.5% (aprox)")
