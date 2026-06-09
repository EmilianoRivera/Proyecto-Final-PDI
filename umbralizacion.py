import cv2
import numpy as np
import matplotlib.pyplot as plt

# =========================================================================
# 1. PASO ANTERIOR: Generar la máscara de rocas con el Mega Closing
# =========================================================================
ruta_bordes_rocas = 'C:\\Users\\Emiliano\\Documents\\ESCOM\\SEMESTRE 4\\PDI\\Proyecto\\bordes_sin_frijoles.png'
img_bordes = cv2.imread(ruta_bordes_rocas, cv2.IMREAD_GRAYSCALE)

if img_bordes is None:
    print("Error: No se pudo cargar la imagen de bordes. Revisa la ruta.")
else:
    # Umbralizamos y aplicamos el Closing Gigante (35x35) que armamos antes
    _, binaria = cv2.threshold(img_bordes, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel_morf = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))
    mascara_rocas = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel_morf)

    # =========================================================================
    # 2. NUEVO PASO: Cargar Imagen Original a Color y Aplicar AND
    # =========================================================================
    ruta_original = 'C:\\Users\\Emiliano\\Documents\\ESCOM\\SEMESTRE 4\\PDI\\Proyecto\\beans.jpg'
    img_original = cv2.imread(ruta_original)

    if img_original is None:
        print("Error: No se pudo cargar la imagen original 'beans.jpg'.")
    else:
        # --- OPCIÓN A: Extraer SOLO las rocas a color ---
        # El AND recortará los píxeles de beans.jpg donde la máscara sea blanca
        solo_rocas_color = cv2.bitwise_and(img_original, img_original, mask=mascara_rocas)
        cv2.imwrite('solo_rocas.png', solo_rocas_color)

        # --- OPCIÓN B: ELIMINAR LAS ROCAS (Dejar solo los frijoles) ---
        # Invertimos la máscara de las rocas (lo blanco se hace negro y viceversa)
        mascara_frijoles = cv2.bitwise_not(mascara_rocas)
        
        # Creamos un fondo completamente blanco del mismo tamaño que la foto
        fondo_blanco = np.ones_like(img_original) * 255
        
        # Con np.where, si la máscara es blanca (255) ponemos el frijol original, 
        # si es negra (0) ponemos fondo blanco. ¡Adiós piedras!
        solo_frijoles_limpios = np.where(mascara_frijoles[:, :, None] == 255, img_original, fondo_blanco)
        cv2.imwrite('solo_frijoles_limpios.png', solo_frijoles_limpios)
        
        print("¡Operaciones AND completadas! Imágenes guardadas en tu carpeta.")

        # =========================================================================
        # 3. MOSTRAR RESULTADOS
        # =========================================================================
        # Convertimos de BGR a RGB para que Matplotlib muestre bien los colores reales
        original_rgb = cv2.cvtColor(img_original, cv2.COLOR_BGR2RGB)
        rocas_rgb = cv2.cvtColor(solo_rocas_color, cv2.COLOR_BGR2RGB)
        frijoles_rgb = cv2.cvtColor(solo_frijoles_limpios, cv2.COLOR_BGR2RGB)

        plt.figure(figsize=(15, 5))

        plt.subplot(1, 3, 1)
        # Mostramos la máscara que usamos para el corte
        plt.title("1. Máscara de Rocas Rellena")
        plt.imshow(mascara_rocas, cmap='gray')
        plt.axis('off')

        plt.subplot(1, 3, 2)
        # Resultado del AND directo
        plt.title("2. AND Directo (Solo Rocas)")
        plt.imshow(rocas_rgb)
        plt.axis('off')

        plt.subplot(1, 3, 3)
        # Resultado de la eliminación con fondo blanco
        plt.title("3. AND Invertido (Frijoles Limpios)")
        plt.imshow(frijoles_rgb)
        plt.axis('off')

        plt.tight_layout()
        plt.show()