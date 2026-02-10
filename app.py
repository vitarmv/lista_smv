import streamlit as st
import re
import math

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Remarcador de Precios v3",
    page_icon="🚀",
    layout="wide"
)

# --- LÓGICA DE NEGOCIO (ACTUALIZADA) ---
def calcular_nuevo_precio(precio_original):
    p = float(precio_original)
    markup = 0
    
    # 1. Rango Bajo ($1 - $29)
    if p < 10:
        markup = 0.50
    elif 10 <= p < 30:
        markup = 2.00
        
    # 2. Rango Medio ($30 - $119)
    elif 30 <= p < 120:
        markup = 5.00
        
    # 3. Rango Dividido ($120 - $219) [MODIFICADO]
    elif 120 <= p < 150:
        markup = 10.00
    elif 150 <= p < 220:
        markup = 15.00
        
    # 4. Rango Continuación ($220 - $289)
    elif 220 <= p < 290:
        markup = 15.00 # (Nota: Se junta con el anterior, efectivamente de 150 a 290 es +15)

    # 5. Rango Dividido ($290 - $414) [MODIFICADO]
    elif 290 <= p < 355:
        markup = 20.00
    elif 355 <= p < 415:
        markup = 25.00
        
    # 6. Rango Medio-Alto ($415 - $509)
    elif 415 <= p < 510:
        markup = 30.00
        
    # 7. Rango Alto ($510 - $999)
    elif 510 <= p < 615:
        # Corte en $550 para definir si es 30 o 35
        markup = 30.00 if p < 550 else 35.00
    elif 615 <= p < 800:
        markup = 40.00
    elif 800 <= p < 1000:
        markup = 50.00
        
    # 8. Rango Premium (Más de $1,000)
    else:
        # Aplica un 5.5% de margen y redondea
        raw_markup = p * 0.055
        markup = round(raw_markup / 5) * 5

    return p + markup

def procesar_whatsapp(texto):
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

st.title("🚀 Traductor de Precios Mayorista -> Cliente")
st.markdown("### 📋 Pega tu lista de WhatsApp abajo")

col1, col2 = st.columns(2)

with col1:
    input_text = st.text_area("⬇️ Entrada (Precios Costo)", height=500, placeholder="Ejemplo:\n🔥iPhone 15 128GB *$630*\nParlante JBL *$6.5*")

with col2:
    if input_text:
        output_text = procesar_whatsapp(input_text)
        st.text_area("✅ Salida (Precios Venta)", value=output_text, height=500)
        st.success("¡Precios actualizados con los nuevos rangos!")
    else:
        st.info("Esperando texto...")

# --- BARRA LATERAL (REFERENCIA) ---
with st.sidebar:
    st.header("📊 Tabla de Aumentos Actualizada")
    st.write("• **$1 - $9**: +$0.50")
    st.write("• **$10 - $29**: +$2.00")
    st.write("• **$30 - $119**: +$5.00")
    st.write("• **$120 - $149**: +$10.00")
    st.write("• **$150 - $289**: +$15.00")
    st.write("• **$290 - $354**: +$20.00")
    st.write("• **$355 - $414**: +$25.00")
    st.write("• **$415 - $509**: +$30.00")
    st.write("• **$510+**: (Escala estándar)")
