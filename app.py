import streamlit as st
import re
import math
import openpyxl
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Remarcador Pro v7",
    page_icon="💎",
    layout="wide"
)

# ==========================================
#        LÓGICA DE CÁLCULO (COMÚN)
# ==========================================
def calcular_precio_venta(valor):
    try:
        # 1. Limpieza de texto a número
        if isinstance(valor, str):
            limpio = valor.replace('$', '').replace(',', '').replace('USD', '').strip()
            # Si es vacío o texto sin números, devolvemos original
            if not limpio: return valor
            p = float(limpio)
        else:
            p = float(valor)
            
        # 2. Si no es un número válido (NaN), devolvemos original
        if p is None or math.isnan(p): return valor
    except:
        return valor

    markup = 0
    # --- TU TABLA DE AUMENTOS ---
    if p < 10: markup = 0.50
    elif 10 <= p < 30: markup = 2.00
    elif 30 <= p < 120: markup = 5.00
    elif 120 <= p < 150: markup = 10.00
    elif 150 <= p < 290: markup = 15.00
    elif 290 <= p < 355: markup = 20.00
    elif 355 <= p < 415: markup = 25.00
    elif 415 <= p < 510: markup = 30.00
    elif 510 <= p < 615: markup = 30.00 if p < 550 else 35.00
    elif 615 <= p < 800: markup = 40.00
    elif 800 <= p < 1000: markup = 50.00
    else:
        # > $1000: 5.5% redondeado a 5
        raw_markup = p * 0.055
        markup = round(raw_markup / 5) * 5

    return p + markup

# ==========================================
#        FUNCIÓN 1: PROCESAR TEXTO
# ==========================================
def procesar_texto_whatsapp(texto):
    lineas = texto.splitlines()
    resultado = []
    
    for linea in lineas:
        # Busca precios como *$500*, $500, $500.00
        match = re.search(r'(\*\$|\$)([\d\.,]+)(\*?)', linea)
        if match:
            try:
                precio_str = match.group(2).replace(',', '')
                precio_base = float(precio_str)
                precio_nuevo = calcular_precio_venta(precio_base)
                
                # Formateo (sin decimales si es entero)
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

# ==========================================
#        FUNCIÓN 2: PROCESAR EXCEL
# ==========================================
def procesar_excel_preservando_formato(uploaded_file, columna_letra, fila_inicio):
    # Carga el archivo manteniendo estilos
    wb = openpyxl.load_workbook(uploaded_file)
    ws = wb.active # Toma la hoja activa
    
    # Convierte letra a índice (A=1, B=2, C=3...)
    col_idx = openpyxl.utils.column_index_from_string(columna_letra)
    
    cambios = 0
    
    # Recorre solo la columna indicada desde la fila indicada
    for row in ws.iter_rows(min_row=fila_inicio, min_col=col_idx, max_col=col_idx):
        celda = row[0]
        valor_original = celda.value
        
        # Si la celda tiene un valor, intentamos calcular
        if valor_original is not None:
            nuevo_precio = calcular_precio_venta(valor_original)
            
            # Si el cálculo devolvió un número diferente, actualizamos
            if nuevo_precio != valor_original:
                celda.value = nuevo_precio
                cambios += 1
                
    return wb, cambios

# ==========================================
#            INTERFAZ GRÁFICA
# ==========================================

st.title("💎 Remarcador Pro v7")

# Creamos las pestañas
tab1, tab2 = st.tabs(["📝 Texto WhatsApp", "📂 Archivo Excel (Formato Intacto)"])

# --- PESTAÑA 1: WHATSAPP ---
with tab1:
    st.markdown("### Copia y pega tu lista de WhatsApp")
    col1, col2 = st.columns(2)
    with col1:
        input_text = st.text_area("⬇️ Entrada (Precios Costo)", height=500, placeholder="Pega aquí tu mensaje...")
    with col2:
        if input_text:
            output_text = procesar_texto_whatsapp(input_text)
            st.text_area("✅ Salida (Precios Venta)", value=output_text, height=500)
        else:
            st.info("Esperando texto...")

# --- PESTAÑA 2: EXCEL ---
with tab2:
    st.markdown("### Edita tu Excel sin romper el diseño")
    uploaded_file = st.file_uploader("Sube tu archivo original (.xlsx)", type=["xlsx"])
    
    if uploaded_file:
        st.info("Configuración de Coordenadas:")
        c1, c2 = st.columns(2)
        with c1:
            col_letra = st.text_input("Letra de la Columna PRECIO", value="C").upper()
        with c2:
            fila_inicio = st.number_input("Número de Fila donde empiezan los datos", min_value=1, value=6)
            
        if st.button("🚀 Remarcar Excel"):
            try:
                wb_res, n_cambios = procesar_excel_preservando_formato(uploaded_file, col_letra, fila_inicio)
                
                if n_cambios > 0:
                    st.success(f"✅ Se actualizaron {n_cambios} precios.")
                    
                    # Guardar para descarga
                    output = BytesIO()
                    wb_res.save(output)
                    datos = output.getvalue()
                    
                    st.download_button(
                        label="📥 Descargar Excel Remarcado",
                        data=datos,
                        file_name="Lista_Precios_Venta.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.warning("⚠️ No se cambiaron precios. Revisa si la Letra de Columna y Fila son correctas.")
            except Exception as e:
                st.error(f"Error procesando el archivo: {e}")

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
