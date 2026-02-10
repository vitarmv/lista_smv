import streamlit as st
import re
import math
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Remarcador Pro v6",
    page_icon="💎",
    layout="wide"
)

# --- LÓGICA DE NEGOCIO ---
def calcular_nuevo_precio(valor):
    # 1. Intentamos convertir el valor a número (float)
    try:
        # Si es texto, limpiamos símbolos de moneda, comas, etc.
        if isinstance(valor, str):
            limpio = valor.replace('$', '').replace(',', '').replace('USD', '').strip()
            # Si queda vacío después de limpiar, devolvemos el original
            if not limpio:
                return valor
            p = float(limpio)
        else:
            # Si ya es número o NaN
            p = float(valor)
    except:
        # Si falla la conversión (ej: es un título como "OFERTAS"), devolvemos tal cual
        return valor

    # 2. Si el número no es válido (NaN), devolvemos el original
    if math.isnan(p):
        return valor

    markup = 0
    
    # --- ESCALAS DE PRECIOS ---
    if p < 10:
        markup = 0.50
    elif 10 <= p < 30:
        markup = 2.00
    elif 30 <= p < 120:
        markup = 5.00
    # Rango dividido
    elif 120 <= p < 150:
        markup = 10.00
    elif 150 <= p < 290: 
        markup = 15.00 
    # Rango dividido
    elif 290 <= p < 355:
        markup = 20.00
    elif 355 <= p < 415:
        markup = 25.00
    elif 415 <= p < 510:
        markup = 30.00
    # Rango Alto
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
                
                # Formato final
                if isinstance(precio_nuevo, (int, float)):
                    if precio_nuevo.is_integer():
                        precio_final_str = f"{int(precio_nuevo):,}"
                    else:
                        precio_final_str = f"{precio_nuevo:,.2f}"
                    
                    bloque_original = match.group(0)
                    bloque_nuevo = f"{match.group(1)}{precio_final_str}{match.group(3)}"
                    linea_nueva = linea.replace(bloque_original, bloque_nuevo)
                    resultado.append(linea_nueva)
                else:
                    resultado.append(linea)
            except:
                resultado.append(linea)
        else:
            resultado.append(linea)
    return "\n".join(resultado)

# --- FUNCIÓN DE LECTURA SEGURA ---
def cargar_archivo(uploaded_file):
    try:
        # Intentamos leer como Excel primero, forzando todo a texto (dtype=str)
        # Esto evita el error "cannot convert float NaN to integer"
        if uploaded_file.name.endswith('.xlsx'):
            try:
                return pd.read_excel(uploaded_file, dtype=str)
            except:
                # Si falla, puede ser un CSV disfrazado de Excel (pasa mucho)
                uploaded_file.seek(0)
                return pd.read_csv(uploaded_file, dtype=str, sep=None, engine='python')
        
        # Si es CSV
        elif uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file, dtype=str, sep=None, engine='python')
            
        else:
            return pd.read_excel(uploaded_file, dtype=str)
            
    except Exception as e:
        st.error(f"Error crítico leyendo el archivo: {e}")
        return None

# --- INTERFAZ ---

st.title("💎 Remarcador de Precios Mayorista")

tab1, tab2 = st.tabs(["📝 Texto WhatsApp", "📂 Archivo Excel"])

# --- MÓDULO 1: WHATSAPP ---
with tab1:
    st.markdown("### Copia y pega tu lista de WhatsApp")
    col1, col2 = st.columns(2)
    with col1:
        input_text = st.text_area("⬇️ Entrada (Precios Costo)", height=500, placeholder="Pega aquí...")
    with col2:
        if input_text:
            output_text = procesar_texto_whatsapp(input_text)
            st.text_area("✅ Salida (Precios Venta)", value=output_text, height=500)
        else:
            st.info("Esperando texto...")

# --- MÓDULO 2: EXCEL ---
with tab2:
    st.markdown("### Sube tu archivo (Excel o CSV)")
    uploaded_file = st.file_uploader("Sube tu archivo", type=["xlsx", "xls", "csv"])
    
    if uploaded_file:
        df = cargar_archivo(uploaded_file)
        
        if df is not None:
            st.write("Vista previa (Primeras filas):")
            st.dataframe(df.head(3))
            
            columnas = df.columns.tolist()
            col_precio = st.selectbox("¿Cuál es la columna que tiene el PRECIO?", columnas)
            
            if st.button("🚀 Calcular Nuevos Precios"):
                try:
                    nombre_nueva_col = f"{col_precio} (Venta)"
                    df[nombre_nueva_col] = df[col_precio].apply(calcular_nuevo_precio)
                    
                    st.success("¡Cálculo terminado!")
                    st.dataframe(df.head())
                    
                    # Descarga
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)
                    datos_excel = output.getvalue()
                    
                    st.download_button(
                        label="📥 Descargar Excel Listo",
                        data=datos_excel,
                        file_name="lista_precios_venta.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"Error al procesar los datos: {e}")

# --- BARRA LATERAL ---
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
