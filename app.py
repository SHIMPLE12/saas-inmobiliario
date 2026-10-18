if uploaded_files:
        st.info(f"📸 Total de fotos seleccionadas: **{len(uploaded_files)}**")
        
        if st.button("🚀 Procesar Lote Completo"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            zip_buffer = io.BytesIO()
            loaded_wm = Image.open(watermark_file) if watermark_file else None

            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for idx, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Procesando imagen {idx+1}/{len(uploaded_files)}: {uploaded_file.name}")
                    
                    try:
                        # Abrir directamente desde el buffer del archivo subido
                        uploaded_file.seek(0)
                        with Image.open(uploaded_file) as img:
                            img = ImageOps.exif_transpose(img)
                            img = img.convert("RGB")

                            # Redimensionar de inmediato para minimizar el consumo de memoria
                            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                            # 1. Filtro de Realce
                            if enable_enhancement:
                                img = ImageEnhance.Brightness(img).enhance(brightness_factor)
                                img = ImageEnhance.Contrast(img).enhance(contrast_factor)

                            # 2. Marca de agua
                            if loaded_wm:
                                img = apply_watermark(img, loaded_wm, wm_position, wm_opacity, wm_color_option)

                            # 3. Nombre SEO
                            clean_seo_name = seo_prefix.strip().replace(" ", "-").lower()
                            new_filename = f"{clean_seo_name}-{idx+1}.jpg"

                            # Guardar directamente a bytes comprimidos
                            out_buffer = io.BytesIO()
                            img.save(out_buffer, format="JPEG", quality=jpeg_quality, optimize=True)
                            
                            zip_file.writestr(new_filename, out_buffer.getvalue())
                            out_buffer.close()
                            
                            del img
                            gc.collect()

                    except Exception as e:
                        st.error(f"Error procesando {uploaded_file.name}: {e}")

                    progress_bar.progress((idx + 1) / len(uploaded_files))

            if loaded_wm:
                loaded_wm.close()

            status_text.success("✅ ¡Lote procesado con éxito!")
            
            st.download_button(
                label="📥 Descargar todo en archivo ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"lote-optimizado-{seo_prefix}.zip",
                mime="application/zip"
            )
