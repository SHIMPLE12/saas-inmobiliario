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
        
        has_alpha = any(item[3] < 255 for item in datas)

        if has_alpha:
            for item in datas:
                if color_option == "Blanco" and item[3] > 0:
                    new_data.append((255, 255, 255, item[3]))
                else:
                    new_data.append(item)
        else:
            bg_color = datas[0] 
            for item in datas:
                if abs(item[0] - bg_color[0]) < 40 and abs(item[1] - bg_color[1]) < 40 and abs(item[2] - bg_color[2]) < 40:
                    new_data.append((255, 255, 255, 0)) 
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
        target_wm_w = int(base_img.width * 0.20)
        aspect_ratio = wm_h / wm_w
        target_wm_h = int(target_wm_w * aspect_ratio)
        
        temp_w = target_wm_w * supersample_factor
        temp_h = target_wm_h * supersample_factor
        wm_resized = wm_img.resize((temp_w, temp_h), Image.Resampling.LANCZOS)
        wm_resized = wm_resized.resize((target_wm_w, target_wm_h), Image.Resampling.LANCZOS)

        # Enfoque equilibrado para máxima nitidez sin artefactos
        enhancer_sharpness = ImageEnhance.Sharpness(wm_resized)
        wm_resized = enhancer_sharpness.enhance(1.3)
        # --------------------------------------------------------

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

    # ==========================================
    # PROCESAMIENTO DEL LOTE (VERIFICACIÓN INDEPENDIENTE)
    # ==========================================
    if uploaded_files:
        st.info(f"📸 Total de fotos seleccionadas: **{len(uploaded_files)}**")
        
        if st.button("🚀 Procesar Lote Completo"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            zip_buffer = io.BytesIO()
            loaded_wm = Image.open(watermark_file) if watermark_file else None

            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for idx, file in enumerate(uploaded_files):
                    status_text.text(f"Procesando imagen {idx+1}/{len(uploaded_files)}: {file.name}")
                    
                    img = Image.open(file)
                    img = ImageOps.exif_transpose(img)

                    # 1. Filtro de Realce
                    if enable_enhancement:
                        img = ImageEnhance.Brightness(img).enhance(brightness_factor)
                        img = ImageEnhance.Contrast(img).enhance(contrast_factor)

                    # 2. Redimensionar
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                    # 3. Marca de agua (solo si se ha subido un logo)
                    if loaded_wm:
                        img = apply_watermark(img, loaded_wm, wm_position, wm_opacity, wm_color_option)
                    else:
                        img = img.convert("RGB")

                    # 4. Nombre SEO
                    clean_seo_name = seo_prefix.strip().replace(" ", "-").lower()
                    new_filename = f"{clean_seo_name}-{idx+1}.jpg"

                    out_buffer = io.BytesIO()
                    img.save(out_buffer, format="JPEG", quality=jpeg_quality, optimize=True)
                    
                    zip_file.writestr(new_filename, out_buffer.getvalue())
                    progress_bar.progress((idx + 1) / len(uploaded_files))

            status_text.success("✅ ¡Lote procesado con éxito!")
            
            st.download_button(
                label="📥 Descargar todo en archivo ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"lote-optimizado-{seo_prefix}.zip",
                mime="application/zip"
            )
