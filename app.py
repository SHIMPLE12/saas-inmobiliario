if uploaded_files:
        st.info(f"📸 Total de fotos seleccionadas: **{len(uploaded_files)}**")
        
        if st.button("🚀 Procesar Lote Completo"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            loaded_wm = Image.open(watermark_file) if watermark_file else None

            # 1. Crear archivo ZIP en DISCO (Evita acumular RAM con lotes gigantes)
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

                            # REDIMENSIONAR PRIMERO
                            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                            # 1. Filtro de Realce
                            if enable_enhancement:
                                img = ImageEnhance.Brightness(img).enhance(brightness_factor)
                                img = ImageEnhance.Contrast(img).enhance(contrast_factor)

                            # 2. Marca de agua
                            if loaded_wm:
                                img = apply_watermark(img, loaded_wm, wm_position, wm_opacity, wm_color_option)
                            
                            # Asegurar que está en RGB antes de guardar como JPEG
                            if img.mode != "RGB":
                                img = img.convert("RGB")

                            # 3. Nombre SEO
                            clean_seo_name = seo_prefix.strip().replace(" ", "-").lower()
                            new_filename = f"{clean_seo_name}-{idx+1}.jpg"

                            out_buffer = io.BytesIO()
                            img.save(out_buffer, format="JPEG", quality=jpeg_quality, optimize=True)
                            
                            # Escribir directamente al archivo temporal en disco
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

            status_text.success("✅ ¡Lote procesado con éxito!")
            
            # Leer desde disco para ofrecer el botón de descarga
            with open(tmp_zip_path, "rb") as f:
                zip_bytes = f.read()

            st.download_button(
                label="📥 Descargar todo en archivo ZIP",
                data=zip_bytes,
                file_name=f"lote-optimizado-{seo_prefix}.zip",
                mime="application/zip"
            )

            # Limpiar archivo temporal
            try:
                os.remove(tmp_zip_path)
            except Exception:
                pass
