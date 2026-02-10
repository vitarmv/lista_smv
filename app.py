import streamlit as st
import openpyxl
from io import BytesIO
import math

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Remarcador Pro - Formato Intacto", page_icon="💎", layout="wide")

# --- LÓGICA DE PRECIOS (TU FORMULA) ---
def calcular_precio_venta(precio_costo):
    try:
        # Limpieza por si viene texto o sucios
        if isinstance(precio_costo, str):
            limpio = precio_costo.replace('$', '').replace(',', '').strip()
            if not limpio: return precio_costo
            p = float(limpio)
        else:
            p = float(precio_costo)
            
        if p is None or math.isnan(p): return precio_costo
    except:
        return precio_costo

    markup = 0
    # --- ESCALAS ---
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

# --- FUNCIÓN DE EDICIÓN EXCEL (PRESERVA FORMATO) ---
def procesar_excel_preservando_formato(uploaded_file, columna_letra, fila_inicio):
    # Cargamos el libro de trabajo (Workbook) completo
    wb = openpyxl.load_workbook(uploaded_file)
    ws = wb.active # Hoja activa
    
    # Convertir letra de columna a índice (ej: 'C' -> 3)
    col_idx = openpyxl.utils.column_index_from_string(columna_letra)
    
    cambios = 0
    
    # Iteramos solo sobre la columna indicada, desde la fila de inicio
    # ws.iter_rows devuelve tuplas, por eso tomamos row[0]
    for row in ws.iter_rows(min_row=fila_inicio, min_col=col_idx, max_col=col_idx):
        celda = row[0]
        valor_original = celda.value
        
        # Solo procesamos si hay un valor
        if valor_original is not None:
            # Calculamos nuevo precio
            nuevo_precio = calcular_precio_venta(valor_original)
            
            # Si cambió el valor (es decir, era un número válido), lo actualizamos
            if nuevo_precio != valor_original:
                celda.value = nuevo_precio
                cambios += 1
                
    return wb, cambios

# --- INTERFAZ ---
st.title("💎 Remarcador: Mantiene tu Formato Original")
st.markdown("""
Esta herramienta **edita** los precios directamente en tu archivo Excel sin tocar el diseño, colores o celdas combinadas.
""")

uploaded_file = st.file_uploader("Sube tu Excel original (.xlsx)", type=["xlsx"])

if uploaded_file:
    st.info("Configura dónde están los precios para no tocar el resto:")
    
    col1, col2 = st.columns(2)
    with col1:
        col_letra = st.text_input("1. ¿En qué COLUMNA están los precios? (Letra)", value="C").upper()
    with col2:
        fila_inicio = st.number_input("2. ¿En qué FILA empiezan los datos? (Número)", min_value=1, value=6)
    
    st.caption("Tip: Abre tu Excel y mira la letra de la columna (A, B, C...) y el número de fila donde empieza el primer producto.")

    if st.button("🚀 Remarcar Precios"):
        try:
            # Procesar
            wb_resultado, num_cambios = procesar_excel_preservando_formato(uploaded_file, col_letra, fila_inicio)
            
            if num_cambios > 0:
                st.success(f"✅ ¡Listo! Se actualizaron {num_cambios} precios.")
                
                # Guardar en memoria para descargar
                output = BytesIO()
                wb_resultado.save(output)
                datos = output.getvalue()
                
                st.download_button(
                    label="📥 Descargar Excel Remarcado",
                    data=datos,
                    file_name="Lista_Precios_Venta.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("⚠️ No se encontraron precios para cambiar. Verifica que la Letra de Columna y Fila de Inicio sean correctas.")
                
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
