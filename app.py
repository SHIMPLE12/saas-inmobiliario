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
# CLAVES INDIVIDUALES PARA CLIENTES ACTIVOS
# ==========================================
CLAVES_ACTIVAS = [
    "AgenciaSol-2026",    # Cliente 1
    "FincasGarcia-2026",  # Cliente 2
    "gesnivalls-2026",    # Cliente 3
]

def verificar_password():
    """Comprueba si la clave introducida está en la lista de clientes activos."""
    def password_entered():
        if st.session_state["password_input"].strip() in CLAVES_ACTIVAS:
            st.session_state["autenticado"] = True
            st.session_state["error_pass"] = False
        else:
            st.session_state["autenticado"] = False
            st.session_state["error_pass"] = True

    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        st.subheader("🔐 Acceso Exclusivo a la Plataforma")
        st.text_input(
            "Introduce tu contraseña de cliente:",
            type="password",
            key="password_input",
            on_change=password_entered
        )
        if st.session_state.get("error_pass", False):
            st.error("❌ Contraseña no válida o suscripción inactiva.")
        return False
    else:
        return True

# ==========================================
# CONTROL DE ACCESO
# ==========================================
if verificar_password():

    # ------------------------------------------
    # A PARTIR DE AQUÍ SOLO SE MUESTRA SI HA INTRODUCIDO LA CONTRASEÑA CORRECTA
    # ------------------------------------------

    st.title("🏠 Procesador Profesional de Imágenes Inmobiliarias")
    st.write("Sube tus lotes de fotos para redimensionar, mejorar luz, renombrar para SEO y colocar tu logo en segundos.")

    st.sidebar.header("⚙️ Configuración del Lote")

    # 1. Configuración de Marca de Agua
    st.sidebar.subheader("1. Marca de Agua / Logo")
    watermark_file = st.sidebar.file_uploader("Subir Logo (PNG transparente recomendado)", type=["png", "jpg", "jpeg"])
    wm_position = st.sidebar.selectbox("Posición del Logo", ["Centro", "Inferior Derecha", "Inferior Izquierda", "Superior Derecha", "Superior Izquierda"])
    wm_opacity = st.sidebar.slider("Opacidad del Logo (%)", 10, 100, 80)

    # Opción: Color de la marca de agua
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
    uploaded_files = st.file_uploader(
        "Selecciona o arrastra las fotos del inmueble (soporta JPG, PNG, HEIC)",
        type=["jpg", "jpeg", "png", "heic", "heif"],
        accept_multiple_files=True
    )

    def apply_watermark(base_img, wm_img, position, opacity_pct, color_option):
        base_img = base_img.convert("RGBA")
        wm_img = wm_img.convert("RGBA")

        # --- LIMPIEZA PROFESIONAL SIN RUIDO NI HALOS ---
        datas = wm_img.getdata()
        new_data = []
        
        # Detectar si la imagen cargada ya posee canal de transparencia real
        has_alpha = any(item[3] < 255 for item in datas)

        if has_alpha:
            # Si el PNG ya es transparente de origen, no forzamos borrado para evitar ruido
            for item in datas:
                if color_option == "Blanco" and item[3] > 0:
                    new_data.append((255, 255, 255, item[3]))
                else:
                    new_data.append(item)
        else:
            # Si tiene fondo sólido rectangular (ej: verde, blanco, etc.)
            bg_color = datas[0] # Tomamos la esquina superior izquierda
            for item in datas:
                # Comprobación de tolerancia de color estricta para eliminar el fondo limpiamente
                if abs(item[0] - bg_color[0]) < 40 and abs(item[1] - bg_color[1]) < 40 and abs(item[2] - bg_color[2]) < 40:
                    new_data.append((255, 255, 255, 0)) # Transparente
                else:
                    if color_option == "Blanco":
                        new_data.append((255, 255, 255, item[3]))
                    else:
                        new_data.append(item)

        wm_img.putdata(new_data)
        # -----------------------------------------------

        # --- REDIMENSIONADO DE ALTA NITIDEZ CON SUPERMUESTREO ---
        supersample_factor = 2 
        wm_w, wm_h = wm_img.size
        target_wm
