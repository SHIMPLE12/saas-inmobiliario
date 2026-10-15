import streamlit as st
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)
import io
from io import BytesIO
import os
import zipfile
from PIL import Image, ImageEnhance, ImageOps
import streamlit as st
import streamlit.components.v1 as components

# Intentamos importar pillow_heif por si suben fotos nativas de iPhone (.heic)
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

st.set_page_config(
    page_title="Optimizador Inmobiliario - SaaS",
    layout="centered"
)

# --- CSS Y JAVASCRIPT PARA ELIMINAR TOTALMENTE INSIGNIAS Y MENÚS EXTERNOS ---
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stToolbar"] {display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}
    .stAppDeployButton {display: none !important;}
    div[data-testid="stConnectionStatus"] {display: none !important;}
    footer, .viewerBadge_container__1QSob, div.viewerBadge_link__1S137 {
        display: none !important; 
        visibility: hidden !important; 
        pointer-events: none !important;
    }
    </style>
    
    <script>
    // Script para eliminar dinámicamente cualquier insignia flotante de Streamlit
    const removeBadge = () => {
        const badges = window.parent.document.querySelectorAll('.viewerBadge_container__1QSob, .stAppDeployButton, footer');
        badges.forEach(el => el.remove());
    };
    setInterval(removeBadge, 500);
    </script>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("🏡 Optimizador Inmobiliario por Lotes")
st.write("Sube el lote de fotos de tu inmueble, ajusta la posición lateral, la opacidad y el color del logo.")

# 1. Subida de archivos múltiples (Soporte amplio para formatos de móvil y PC)
uploaded_images = st.file_uploader(
    "1. Sube el lote de fotos del piso (JPG, PNG, WEBP, HEIC)",
    type=["jpg", "jpeg", "png", "webp", "heic", "JPG", "JPEG", "PNG", "WEBP", "HEIC"],
    accept_multiple_files=True
)

uploaded_logo = st.file_uploader(
    "2. Sube el logo de la inmobiliaria (PNG, JPG)",
    type=["png", "PNG", "jpg", "JPG", "jpeg", "JPEG"]
)

# Configuración del logo
st.subheader("⚙️ Configuración del Logo / Marca de Agua")
col1, col2, col3 = st.columns(3)

with col1:
    posicion = st.selectbox(
        "Ubicación del logo",
        [
            "Esquina Inferior Derecha",
            "Esquina Inferior Izquierda",
            "Esquina Superior Derecha",
            "Esquina Superior Izquierda",
            "Centro"
        ]
    )

with col2:
    estilo_color = st.selectbox(
        "Color del Logo",
        ["Blanco (Efecto Agua)", "Color Original"],
        help="La opción 'Blanco' aísla el texto y el icono eliminando cualquier fondo sólido."
    )

with col3:
    opacidad_pct = st.slider(
        "Opacidad / Intensidad",
        min_value=10,
        max_value=100,
        value=35,
        step=5,
        help="30-40% es perfecto para un acabado tenue y profesional."
    )

if uploaded_images and uploaded_logo:
    if st.button(f"🚀 Procesar Lote ({len(uploaded_images)} fotos)"):
        try:
            # Cargar logo base en RGBA
            logo_raw = Image.open(uploaded_logo).convert("RGBA")

            # --- TRATAMIENTO QUIRÚRGICO DE FONDO ---
            bg_color = logo_raw.getpixel((0, 0))[:3]
            datas = logo_raw.getdata()
            new_pixels = []
            alpha_factor = opacidad_pct / 100.0

            for item in datas:
                r, g, b = item[0], item[1], item[2]
                orig_alpha = item[3] if len(item) > 3 else 255
                
                # Detectar si el píxel pertenece al fondo (basado en la esquina)
                is_background = (
                    abs(r - bg_color[0]) < 45 and 
                    abs(g - bg_color[1]) < 45 and 
                    abs(b - bg_color[2]) < 45
                )

                if is_background:
                    new_pixels.append((255, 255, 255, 0))  # Fondo transparente
                else:
                    if estilo_color == "Blanco (Efecto Agua)":
                        alpha_val = int(255 * alpha_factor)
                        new_pixels.append((255, 255, 255, alpha_val))
                    else:
                        alpha_val = int(orig_alpha * max(alpha_factor, 0.85))
                        new_pixels.append((r, g, b, alpha_val))

            logo_raw.putdata(new_pixels)
            logo_img = logo_raw

            zip_buffer = BytesIO()

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                st.markdown("---")
                st.subheader("📸 Resultados procesados:")

                fotos_procesadas = 0

                for idx, uploaded_file in enumerate(uploaded_images):
                    try:
                        base_img = Image.open(uploaded_file)
                        base_img = ImageOps.exif_transpose(base_img).convert("RGB")

                        target_width = 1500
                        w_percent = (target_width / float(base_img.size[0]))
                        target_height = int(float(base_img.size[1]) * float(w_percent))

                        base_resized = base_img.resize(
                            (target_width, target_height), Image.Resampling.LANCZOS
                        )

                        logo_target_width = int(target_width * 0.22)
                        logo_percent = (logo_target_width / float(logo_img.size[0]))
                        logo_target_height = int(float(logo_img.size[1]) * float(logo_percent))

                        logo_resized = logo_img.resize(
                            (logo_target_width, logo_target_height),
                            Image.Resampling.LANCZOS
                        )

                        margin = 35
                        img_w, img_h = base_resized.size
                        logo_w, logo_h = logo_resized.size

                        if posicion == "Esquina Inferior Derecha":
                            pos_x = img_w - logo_w - margin
                            pos_y = img_h - logo_h - margin
                        elif posicion == "Esquina Inferior Izquierda":
                            pos_x = margin
                            pos_y = img_h - logo_h - margin
                        elif posicion == "Esquina Superior Derecha":
                            pos_x = img_w - logo_w - margin
                            pos_y = margin
                        elif posicion == "Esquina Superior Izquierda":
                            pos_x = margin
                            pos_y = margin
                        else:
                            pos_x = (img_w - logo_w) // 2
                            pos_y = (img_h - logo_h) // 2

                        base_resized.paste(logo_resized, (pos_x, pos_y), mask=logo_resized)

                        img_buffer = BytesIO()
                        base_resized.save(img_buffer, format="JPEG", quality=85, optimize=True)
                        img_bytes = img_buffer.getvalue()

                        out_filename = f"foto_optimizada_{idx+1}.jpg"
                        zip_file.writestr(out_filename, img_bytes)

                        size_kb = len(img_bytes) / 1024
                        col_img, col_info = st.columns([2, 1])
                        with col_img:
                            st.image(img_bytes, caption=f"Foto {idx+1}: {out_filename}", use_container_width=True)
                        with col_info:
                            st.write(f"**Peso:** {size_kb:.1f} KB")
                            st.write(f"**Dimensiones:** {target_width}x{target_height} px")
                            st.download_button(
                                label="📥 Descargar foto",
                                data=img_bytes,
                                file_name=out_filename,
                                mime="image/jpeg",
                                key=f"dl_{idx}"
                            )

                        fotos_procesadas += 1

                    except Exception as e:
                        st.error(f"❌ Error al procesar el archivo '{uploaded_file.name}'.")

                zip_file.close()

            if fotos_procesadas > 0:
                zip_buffer.seek(0)
                st.markdown("---")
                st.success(f"✅ ¡Se han procesado las {fotos_procesadas} fotos correctamente!")

                st.download_button(
                    label="📦 Descargar TODO el Lote Optimizado (.ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="lote_fotos_inmueble_optimizadas.zip",
                    mime="application/zip"
                )

        except Exception as general_error:
            st.error("⚠️ Ocurrió un error al procesar el lote.")
