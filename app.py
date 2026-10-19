import gc
import io
import os
import zipfile
import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import pillow_heif

# Registrar el decodificador de HEIC/HEIF de iPhone
pillow_heif.register_heif_opener()

# 1. LA CONFIGURACIÓN DE PÁGINA DEBE SER SIEMPRE LA PRIMERA INSTRUCCIÓN
st.set_page_config(
    page_title="SaaS Inmobiliario - Optimización de Imágenes",
    page_icon="🏠",
    layout="wide"
)

# ==========================================
# CONFIGURACIÓN DE ACCESO Y PLANES
# ==========================================
CLAVES_ACTIVAS = [
    "AgenciaSol-2026",    # Cliente de pago 1
    "FincasGarcia-2026",  # Cliente de pago 2
    "gesnivalls-2026",    # Gesinvallès (Cliente de pago 3)
]

LIMITE_PRUEBA_GRATIS = 10  # Fotos máximas para usuarios en prueba gratuita

st.title("🏠 Procesador Profesional de Imágenes Inmobiliarias")
st.write("Sube tus lotes de fotos para redimensionar, mejorar luz, renombrar para SEO y colocar tu logo en segundos.")

# Barra lateral para configuración y acceso de clientes
st.sidebar.header("⚙️ Configuración del Lote")

# Control de Clientes de Pago en la barra lateral
st.sidebar.subheader("🔐 Área de Clientes")
password_input = st.sidebar.text_input("Introduce tu contraseña SaaS:", type="password")

es_cliente_pagando = password_input.strip() in CLAVES_ACTIVAS

if password_input.strip() != "":
    if es_cliente_pagando:
        st.sidebar.success("✅ ¡Suscripción activa! Lotes ilimitados desbloqueados.")
    else:
        st.sidebar.error("❌ Contraseña incorrecta. Estás en modo de prueba gratuita.")

# 1. Configuración de Marca de Agua
st.sidebar.subheader("1. Marca de Agua / Logo")
watermark_file = st.sidebar.file_uploader("Subir Logo (PNG transparente recomendado)", type=["png", "jpg", "jpeg"])
wm_position = st.sidebar.selectbox("Posición del Logo", ["Centro", "Inferior Derecha", "Inferior Izquierda", "Superior Derecha", "Superior Izquierda"])
wm_opacity = st.sidebar.slider("Opacidad del Logo (%)", 10, 100, 80)
wm_color_option = st.sidebar.selectbox("Color de la Marca de Agua", ["Original (Color del logo)", "Blanco"])

# 2. Configuración SEO
st.sidebar.subheader("2. Renombrado SEO")
seo_prefix = st.sidebar.text_input("Texto SEO (ej: piso-en-venta-madrid)", value="inmueble-oferta")

# 3. Mejora de Luz / Filtro Inmobiliario
st.sidebar.subheader("3. Realce de Luz y Color")
enable_enhancement = st.sidebar.checkbox("Activar Filtro Inmobiliario (Brillo/Luz)", value=True)
brightness_factor = st.sidebar.slider("Brillo / Luz", 0.8, 1.8, 1.25)
contrast_factor = st.sidebar.slider("Contraste", 0.8, 1.5, 1.1)

# 4. Redimensionado y Calidad
st.sidebar.subheader("4. Tamaño y Calidad")
max_width = st.sidebar.number_input("Ancho Máximo (px)", value=1920)
max_height = st.sidebar.number_input("Alto Máximo (px)", value=1080)
jpeg_quality = st.sidebar.slider("Calidad JPEG (%)", 50, 95, 82)

# ZONA DE CARGA DE IMÁGENES
mensaje_carga = "Selecciona o arrastra las fotos (Modo prueba: Máx 10 fotos)" if not es_cliente_pagando else "Selecciona o arrastra las fotos del inmueble (Lotes ilimitados)"
uploaded_files = st.file_uploader(
    mensaje_carga,
    type=["jpg", "jpeg", "png", "heic", "heif"],
    accept_multiple_files=True
)

def apply_watermark(base_img, wm_img, position, opacity_pct, color_option):
    base_img = base_img.convert("RGBA")
    wm_img = wm_img.convert("RGBA")

    datas = wm_img.getdata()
    new_data = []
    bg_color = datas[0] 
    
    for item in datas:
        if abs(item[0] - bg_color[0]) < 35 and abs(item[1] - bg_color[1]) < 35 and abs(item[2] - bg_color[2]) < 35:
            new_data.append((255, 255
