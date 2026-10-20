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

# Inicializar contador de fotos de prueba gratuitas (10 fotos en total)
if "fotos_gratis_disponibles" not in st.session_state:
    st.session_state["fotos_gratis_disponibles"] = 10

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
if not es_cliente_pagando:
    mensaje_carga = f"Selecciona fotos (Prueba gratuita: Te quedan {st.session_state['fotos_gratis_disponibles']} fotos)"
else:
    mensaje_carga = "Selecciona o arrastra las fotos del inmueble (Lotes ilimitados)"

uploaded_files = st.file_uploader(
    mensaje_carga,
    type=["jpg", "jpeg", "png", "heic", "heif"],
    accept_multiple_files=True
)

def apply_watermark(base_img, wm_img, position, opacity_pct, color_option):
    base_img = base_img.convert("RGBA")
    wm_img = wm_img.convert("RGBA")

    wm_w, wm_h = wm_img.size
    target_wm_w = int(base_img.width * 0.20)
    aspect_ratio = wm_h / wm_w
    target_wm_h = int(target_wm_w * aspect_ratio)
    
    wm_resized = wm_img.resize((target_wm_w, target_wm_h), Image.Resampling.LANCZOS)

    if color_option == "Blanco":
        r, g, b, alpha_channel = wm_resized.split()
        wm_white = Image.new("RGBA", wm_resized.size, (255, 255, 255, 255))
        wm_white.putalpha(alpha_channel)
        wm_resized = wm_white

    alpha = wm_resized.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity_pct / 100.0)
    wm_resized.putalpha(alpha)

    margin = int(base_img.width * 0.03)
    if position == "Centro":
        pos = ((base_img.width - target_wm_w) // 2, (base_img.height - target_wm_h) // 2)
    elif position == "Inferior Derecha":
        pos = (base_img.width - target_wm_w - margin, base_img.height - target_wm_h - margin)
    elif position == "Inferior Izquierda":
        pos = (margin, base_img.height - target_wm_h - margin)
    elif position == "Superior Derecha":
        pos = (base_img.width - target_wm_w - margin, margin)
    else:
        pos = (margin, margin)

    transparent = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    transparent.paste(base_img, (0, 0))
    transparent.paste(wm_resized, pos, mask=wm_resized)
    return transparent.convert("RGB")

if uploaded_files:
    if not es_cliente_pagando:
        if st.session_state["fotos_gratis_disponibles"] <= 0:
            st.error("❌ Has agotado tus 10 fotos gratuitas de prueba.")
            st.info("💡 **¿Quieres procesar sin límites?** Introduce tu contraseña de cliente en la barra lateral o adquiere la suscripción profesional en Gumroad:")
            st.link_button("💳 Contratar Suscripción Profesional (22,99 €/mes)", "https://ganpan.gumroad.com/l/idbat")
            st.stop()
        
        if len(uploaded_files) > st.session_state["fotos_gratis_disponibles"]:
            st.warning(f"⚠️ Has seleccionado **{len(uploaded_files)} fotos**, pero solo te quedan **{st.session_state['fotos_gratis_disponibles']} fotos gratuitas** disponibles.")
            st.info("💡 Reduce el número de fotos o adquiere acceso ilimitado:")
            st.link_button("💳 Contratar Suscripción Profesional (22,99 €/mes)", "https://ganpan.gumroad.com/l/idbat")
            st.stop()

    st.info(f"📸 Total de fotos seleccionadas: **{len(uploaded_files)}**")
    
    if st.button("🚀 Procesar Lote Completo"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        loaded_wm = Image.open(watermark_file) if watermark_file else None

        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip_file:
            tmp_zip_path = tmp_zip_file.name

        with zipfile.ZipFile(tmp_zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, file in enumerate(uploaded_files):
                status_text.text(f"Procesando imagen {idx+1}/{len(uploaded_files)}: {file.name}")
                
                try:
                    file.seek(0)
                    with Image.open(file) as img:
                        img = ImageOps.exif_transpose(img)
                        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                        if enable_enhancement:
                            img = ImageEnhance.Brightness(img).enhance(brightness_factor)
                            img = ImageEnhance.Contrast(img).enhance(contrast_factor)

                        if loaded_wm:
                            img = apply_watermark(img, loaded_wm, wm_position, wm_opacity, wm_color_option)
                        
                        if img.mode != "RGB":
                            img = img.convert("RGB")

                        clean_seo_name = seo_prefix.strip().replace(" ", "-").lower()
                        new_filename = f"{clean_seo_name}-{idx+1}.jpg"

                        out_buffer = io.BytesIO()
                        img.save(out_buffer, format="JPEG", quality=jpeg_quality, optimize=True)
                        
                        zip_file.writestr(new_filename, out_buffer.getvalue())
                        
                        out_buffer.close()
                        del out_buffer
                        del img
                        gc.collect()

                except Exception as e:
                    st.error(f"Error procesando {file.name}: {e}")

                progress_bar.progress((idx + 1) / len(uploaded_files))

        if loaded_wm:
            loaded_wm.close()

        if not es_cliente_pagando:
            st.session_state["fotos_gratis_disponibles"] -= len(uploaded_files)

        status_text.success("✅ ¡Lote procesado con éxito!")
        
        with open(tmp_zip_path, "rb") as f:
            zip_bytes = f.read()

        st.download_button(
            label="📥 Descargar todo en archivo ZIP",
            data=zip_bytes,
            file_name=f"lote-optimizado-{seo_prefix}.zip",
            mime="application/zip"
        )

        try:
            os.remove(tmp_zip_path)
        except Exception:
            pass
