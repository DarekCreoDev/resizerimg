import streamlit as st
from PIL import Image
import os
import io
import time
import zipfile

def process_image(image, output_sizes, file_format="WEBP"):
    results = {}
    for size, (width, height, max_size_kb) in output_sizes.items():
        img_copy = image.copy()
        
        # Obliczanie nowej wysokości przy zachowaniu proporcji
        aspect_ratio = img_copy.width / img_copy.height
        new_height = int(width / aspect_ratio)
        
        img_copy = img_copy.resize((width, new_height), Image.LANCZOS)
        
        output_image = io.BytesIO()
        quality = 100
        img_copy.save(output_image, format=file_format, quality=quality)
        
        while output_image.tell() > max_size_kb * 1024 and quality > 0:
            quality -= 5
            output_image = io.BytesIO()
            img_copy.save(output_image, format=file_format, quality=quality)
        
        results[size] = output_image.getvalue()
    return results

def main():
    st.title("Konwerter obrazów")
    st.write("Witamy w narzędziu do konwersji obrazów. Możesz przetwarzać zdjęcia masowo lub pojedynczo. Wybierz odpowiednią opcję z menu po lewej stronie.")

    menu = [
        "Automatycznie dopasowany drugi wymiar",
        "Masowe przetwarzanie",
        "Pojedyncze zdjęcie",
        "Zdjęcia z Midjourney",
        "Niestandardowy rozmiar",
    ]

    choice = st.sidebar.selectbox("Wybierz tryb", menu)

    # Przycisk "Pobierz wszystkie zdjęcia" na górze każdej zakładki
    st.sidebar.markdown("### Po przetworzeniu zdjęcia możesz spakować je do ZIP i pobrać.")
    if st.sidebar.button("Kliknij i przygotuj paczkę, ze zdjęciami.", key="download_all_top"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_name, results in st.session_state.get("processed_images", []):
                for size, img_bytes in results.items():
                    zip_file.writestr(f"{os.path.splitext(file_name)[0]}_{size}.webp", img_bytes)
        
        st.sidebar.download_button(
            label="Pobierz wszystkie zdjęcia",
            data=zip_buffer.getvalue(),
            file_name="wszystkie_zdjecia.zip",
            mime="application/zip",
        )

    if choice == "Automatycznie dopasowany drugi wymiar":
        st.header("Automatycznie dopasowany drugi wymiar - Przetwarzanie zdjęć")
        st.write("Wybierz pliki i określ szerokość dla przetwarzanych zdjęć. Wysokość zostanie dostosowana automatycznie.")

        custom_width = st.number_input(
            "Szerokość (px)", min_value=100, max_value=1920, value=1920
        )
        
        custom_max_size = st.number_input(
            "Maksymalny rozmiar pliku (KB)", min_value=50, max_value=1000, value=100
        )

        file_format = st.selectbox(
            "Format pliku", options=["WEBP", "JPEG", "PNG"], index=0
        )

        uploaded_files = st.file_uploader(
            "Wybierz pliki", type=["jpg", "png"], accept_multiple_files=True
        )

        if uploaded_files:
            # Wyświetlanie aktualnej wysokości obrazu
            
            st.number_input("Aktualna wysokość dla podanej szerokości wynosi: ", int(custom_width / (Image.open(uploaded_files[0]).width / Image.open(uploaded_files[0]).height)))

            if st.button("Przetwórz zdjęcia"):
                st.session_state.new_tab_processing = True
                st.session_state.processed_images = []
            
            if st.session_state.get("new_tab_processing", False):
                progress_bar = st.progress(0)
                start_time = time.time()
                processed_count = 0
                
                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        image = Image.open(uploaded_file)
                        aspect_ratio = image.width / image.height
                        new_height = int(custom_width / aspect_ratio)
                        custom_output_sizes = {
                            "Nowy rozmiar": (custom_width, new_height, custom_max_size)
                        }
                        results = process_image(image, custom_output_sizes, file_format)
                        st.write(f"Przetworzono: {uploaded_file.name}")
                        
                        cols = st.columns(2)
                        preview_image = next(iter(results.values()))
                        with cols[0]:
                            st.image(preview_image, caption="Podgląd", use_column_width=True)
                        
                        with cols[1]:
                            processed_image = Image.open(io.BytesIO(results["Nowy rozmiar"]))
                            st.download_button(
                                label=f"Pobierz {custom_width}x{processed_image.height}.{file_format.lower()}",
                                data=results["Nowy rozmiar"],
                                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{custom_width}x{processed_image.height}.{file_format.lower()}",
                                mime=f"image/{file_format.lower()}",
                            )
                        
                        st.session_state.processed_images.append((uploaded_file.name, results))
                        st.write("---")
                        processed_count += 1
                    except Exception as e:
                        st.error(f"Błąd podczas przetwarzania {uploaded_file.name}: {str(e)}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                end_time = time.time()
                processing_time = end_time - start_time
                st.success(f"Przetworzono {processed_count} z {len(uploaded_files)} plików w {processing_time:.2f} sekund.")

    elif choice == "Masowe przetwarzanie":
        st.header("Masowe przetwarzanie zdjęć")
        st.write("Wybierz pliki, które chcesz przetworzyć. Możesz przesłać wiele plików jednocześnie.")

        output_sizes = {
            "Miniaturka": (600, 400, 50),
            "Banner": (1200, 500, 100),
            "Zdjęcie": (1200, 600, 100),
        }

        uploaded_files = st.file_uploader(
            "Wybierz pliki", type=["jpg", "png"], accept_multiple_files=True
        )

        if uploaded_files:
            if st.button("Przetwórz zdjęcia"):
                st.session_state.bulk_processing = True
                st.session_state.processed_images = []
            
            if st.session_state.get("bulk_processing", False):
                progress_bar = st.progress(0)
                start_time = time.time()
                processed_count = 0
                
                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        image = Image.open(uploaded_file)
                        results = process_image(image, output_sizes)
                        st.write(f"Przetworzono: {uploaded_file.name}")
                        
                        cols = st.columns(3)
                        preview_image = next(iter(results.values()))
                        with cols[0]:
                            st.image(preview_image, caption="Podgląd", use_column_width=True)
                        
                        for idx, (size, img_bytes) in enumerate(results.items()):
                            with cols[(idx + 1) % 3]:
                                st.download_button(
                                    label=f"Pobierz {size}",
                                    data=img_bytes,
                                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                                    mime="image/webp",
                                )
                        
                        st.session_state.processed_images.append((uploaded_file.name, results))
                        st.write("---")
                        processed_count += 1
                    except Exception as e:
                        st.error(f"Błąd podczas przetwarzania {uploaded_file.name}: {str(e)}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                end_time = time.time()
                processing_time = end_time - start_time
                st.success(f"Przetworzono {processed_count} z {len(uploaded_files)} plików w {processing_time:.2f} sekund.")

    elif choice == "Pojedyncze zdjęcie":
        st.header("Przetwarzanie pojedynczego zdjęcia")
        st.write("Wybierz jedno zdjęcie, które chcesz przetworzyć.")

        output_sizes = {
            "Miniaturka": (600, 400, 50),
            "Banner": (1200, 500, 100),
            "Zdjęcie": (1200, 600, 100),
        }

        uploaded_file = st.file_uploader("Wybierz plik", type=["jpg", "png"])

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Oryginalne zdjęcie", use_column_width=True)

            if st.button("Przetwórz"):
                results = process_image(image, output_sizes)
                cols = st.columns(3)
                preview_image = next(iter(results.values()))
                with cols[0]:
                    st.image(preview_image, caption="Podgląd", use_column_width=True)
                
                for i, (size, img_bytes) in enumerate(results.items()):
                    with cols[(i + 1) % 3]:
                        st.download_button(
                            label=f"Pobierz {size}",
                            data=img_bytes,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                            mime="image/webp",
                        )

    elif choice == "Zdjęcia z Midjourney":
        st.header("Przetwarzanie zdjęć z Midjourney")
        st.write("Wybierz pliki PNG z Midjourney, które chcesz przetworzyć.")

        output_sizes = {
            "Miniaturka": (600, 400, 50),
            "Banner": (1200, 500, 100),
            "Zdjęcie": (1200, 600, 100),
        }

        uploaded_files = st.file_uploader(
            "Wybierz pliki PNG z Midjourney", type=["png"], accept_multiple_files=True
        )

        if uploaded_files:
            if st.button("Przetwórz zdjęcia"):
                st.session_state.midjourney_processing = True
                st.session_state.processed_images = []
            
            if st.session_state.get("midjourney_processing", False):
                progress_bar = st.progress(0)
                start_time = time.time()
                processed_count = 0
                
                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        image = Image.open(uploaded_file)
                        results = process_image(image, output_sizes)
                        st.write(f"Przetworzono: {uploaded_file.name}")
                        
                        cols = st.columns(3)
                        preview_image = next(iter(results.values()))
                        with cols[0]:
                            st.image(preview_image, caption="Podgląd", use_column_width=True)
                        
                        for idx, (size, img_bytes) in enumerate(results.items()):
                            with cols[(idx + 1) % 3]:
                                st.download_button(
                                    label=f"Pobierz {size}",
                                    data=img_bytes,
                                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                                    mime="image/webp",
                                )
                        
                        st.session_state.processed_images.append((uploaded_file.name, results))
                        st.write("---")
                        processed_count += 1
                    except Exception as e:
                        st.error(f"Błąd podczas przetwarzania {uploaded_file.name}: {str(e)}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                end_time = time.time()
                processing_time = end_time - start_time
                st.success(f"Przetworzono {processed_count} z {len(uploaded_files)} plików w {processing_time:.2f} sekund.")

    elif choice == "Niestandardowy rozmiar":
        st.header("Przetwarzanie zdjęć w niestandardowym rozmiarze")
        st.write("Wybierz pliki i określ niestandardową szerokość oraz format dla przetwarzanych zdjęć.")

        custom_width = st.number_input(
            "Szerokość (px)", min_value=100, max_value=1920, value=1920
        )

        custom_max_size = st.number_input(
            "Maksymalny rozmiar pliku (KB)", min_value=50, max_value=1000, value=100
        )

        file_format = st.selectbox(
            "Format pliku", options=["WEBP", "JPEG", "PNG"], index=0
        )

        custom_output_sizes = {
            "Niestandardowy": (custom_width, 0, custom_max_size)  # Wysokość zostanie obliczona automatycznie
        }

        uploaded_files = st.file_uploader(
            "Wybierz pliki", type=["jpg", "png"], accept_multiple_files=True
        )

        if uploaded_files:
            if st.button("Przetwórz zdjęcia"):
                st.session_state.custom_processing = True
                st.session_state.processed_images = []
            
            if st.session_state.get("custom_processing", False):
                progress_bar = st.progress(0)
                start_time = time.time()
                processed_count = 0
                
                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        image = Image.open(uploaded_file)
                        aspect_ratio = image.width / image.height
                        new_height = int(custom_width / aspect_ratio)
                        custom_output_sizes = {
                            "Niestandardowy": (custom_width, new_height, custom_max_size)
                        }
                        results = process_image(image, custom_output_sizes, file_format)
                        st.write(f"Przetworzono: {uploaded_file.name}")
                        
                        cols = st.columns(2)
                        preview_image = next(iter(results.values()))
                        with cols[0]:
                            st.image(preview_image, caption="Podgląd", use_column_width=True)
                        
                        with cols[1]:
                            processed_image = Image.open(io.BytesIO(results["Niestandardowy"]))
                            st.download_button(
                                label=f"Pobierz {custom_width}x{processed_image.height}.{file_format.lower()}",
                                data=results["Niestandardowy"],
                                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{custom_width}x{processed_image.height}.{file_format.lower()}",
                                mime=f"image/{file_format.lower()}",
                            )
                        
                        st.session_state.processed_images.append((uploaded_file.name, results))
                        st.write("---")
                        processed_count += 1
                    except Exception as e:
                        st.error(f"Błąd podczas przetwarzania {uploaded_file.name}: {str(e)}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                end_time = time.time()
                processing_time = end_time - start_time
                st.success(f"Przetworzono {processed_count} z {len(uploaded_files)} plików w {processing_time:.2f} sekund.")

if __name__ == "__main__":
    main()
