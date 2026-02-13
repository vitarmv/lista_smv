import streamlit as st
import re
import math
import openpyxl
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Remarcador Pro v9",
    page_icon="💎",
    layout="wide"
)

# ==========================================
#        LÓGICA DE CÁLCULO (ACTUALIZADA)
# ==========================================
def calcular_precio_venta(valor):
    try:
        # 1. Limpieza de texto a número
        if isinstance(valor, str):
            limpio = valor.replace('$', '').replace(',', '').replace('USD', '').strip()
            if not limpio: return valor
            p = float(limpio)
        else:
            p = float(valor)
            
        if p is None or math.isnan(p): return valor
    except:
        return valor

    markup = 0
    
    # --- TABLA DE AUMENTOS v8 ---
    
    # Rangos Bajos
    if p < 10: markup = 0.50
    elif 10 <= p < 30: markup = 2.00
    elif 30 <= p < 120: markup = 5.00
    elif 120 <= p < 150: markup = 10.00
    elif 150 <= p < 290: markup = 15.00
    
    # Rangos Medios
    elif 290 <= p < 355: markup = 20.00
    elif 355 <= p < 415: markup = 25.00
    elif 415 <= p < 510: markup = 30.00
    
    # Rangos Altos
    elif 510 <= p < 615: 
        markup = 30.00 if p < 550 else 35.00
        
    # Nuevo desglose 615-799
    elif 615 <= p < 710:
        markup = 30.00
    elif 710 <= p < 800:
        markup = 35.00
        
    # Nuevo desglose 800-999
    elif 800 <= p < 900:
        markup = 40.00
    elif 900 <= p < 1000:
        markup = 45.00
        
    # Gama Premium
    else:
        # Mayor o igual a 1000
        markup = 55.00

    return p + markup

# ==========================================
#   FUNCIÓN 1: PROCESAR TEXTO (CON LIMPIEZA)
# ==========================================
def procesar_texto_whatsapp(texto):
    lineas = texto.splitlines()
    resultado = []
    
    # Patrón Regex para detectar: [fecha hora] Nombre:
    # Ejemplo: [12/2 10:21 a. m.] José Felixxx:
    patron_chat = r'^\[\d{1,2}/\d{1,2}.*?\] .*?:'

    for linea in lineas:
        # --- PASO DE LIMPIEZA ---
        # Si la línea empieza con el patrón de WhatsApp, lo borramos
        linea_limpia = re.sub(patron_chat, '', linea).strip()
        
        # Si después de limpiar la línea queda vacía (era solo el nombre y fecha), la saltamos
        if not linea_limpia:
            continue
            
        # Usamos la línea limpia para el cálculo
        match = re.search(r'(\*\$|\$)([\d\.,]+)(\*?)', linea_limpia)
        
        if match:
            try:
                precio_str = match.group(2).replace(',', '')
                precio_base = float(precio_str)
                precio_nuevo = calcular_precio_venta(precio_base)
                
                if isinstance(precio_nuevo, (int, float)):
                    if precio_nuevo.is_integer():
                        precio_final_str = f"{int(precio_nuevo):,}"
                    else:
                        precio_final_str = f"{precio_nuevo:,.2f}"
                    
                    bloque_original = match.group(0)
                    bloque_nuevo = f"{match.group(1)}{precio_final_str}{match.group(3)}"
                    
                    # Reemplazamos en la línea limpia
                    linea_final = linea_limpia.replace(bloque_original, bloque_nuevo)
                    resultado.append(linea_final)
                else:
                    resultado.append(linea_limpia)
            except:
                resultado.append(linea_limpia)
        else:
            # Si no hay precio, agregamos la línea tal cual (pero limpia de encabezados)
            resultado.append(linea_limpia)
            
    return "\n".join(resultado)

# ==========================================
#        FUNCIÓN 2: PROCESAR EXCEL
# ==========================================
def procesar_excel_preservando_formato(uploaded_file, columna_letra, fila_inicio):
    wb = openpyxl.load_workbook(uploaded_file)
    ws = wb.active 
    
    col_idx = openpyxl.utils.column_index_from_string(columna_letra)
    
    cambios = 0
    
    for row in ws.iter_rows(min_row=fila_inicio, min_col=col_idx, max_col=col_idx):
        celda = row[0]
        valor_original = celda.value
        
        if valor_original is not None:
            nuevo_precio = calcular_precio_venta(valor_original)
            
            # Verificamos si cambió y es numérico
            if nuevo_precio != valor_original and isinstance(nuevo_precio, (int, float)):
                celda.value = nuevo_precio
                cambios += 1
                
    return wb, cambios

# ==========================================
#            INTERFAZ GRÁFICA
# ==========================================

st.title("💎 Remarcador Pro v9 (Anti-Spam WhatsApp)")

tab1, tab2 = st.tabs(["📝 Texto WhatsApp", "📂 Archivo Excel (Formato Intacto)"])

# --- PESTAÑA 1: WHATSAPP ---
with tab1:
    st.markdown("### Copia y pega tu lista de WhatsApp")
    st.info("💡 Ahora el sistema borra automáticamente líneas tipo: `[12/2 10:21 a. m.] José Felixxx:`")
    
    col1, col2 = st.columns(2)
    with col1:
        input_text = st.text_area("⬇️ Entrada (Con encabezados de chat)", height=500, placeholder="Pega aquí tu conversación completa...")
    with col2:
        if input_text:
            output_text = procesar_texto_whatsapp(input_text)
            st.text_area("✅ Salida (Limpia y Calculada)", value=output_text, height=500)
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
    st.header("📊 Tabla de Aumentos (v8)")
    st.markdown("---")
    st.write("• **$1 - $9**: +$0.50")
    st.write("• **$10 - $29**: +$2.00")
    st.write("• **$30 - $119**: +$5.00")
    st.write("• **$120 - $149**: +$10.00")
    st.write("• **$150 - $289**: +$15.00")
    st.write("• **$290 - $354**: +$20.00")
    st.write("• **$355 - $414**: +$25.00")
    st.write("• **$415 - $509**: +$30.00")
    st.write("• **$510 - $614**: +$30/$35")
    st.markdown("---")
    st.write("• **$615 - $709**: +$30.00")
    st.write("• **$710 - $799**: +$35.00")
    st.write("• **$800 - $899**: +$40.00")
    st.write("• **$900 - $999**: +$45.00")
    st.markdown("---")
    st.write("• **+$1,000**: +$55.00 (Fijo)")
