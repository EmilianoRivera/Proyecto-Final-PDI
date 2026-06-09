import cv2
import numpy as np
import matplotlib.pyplot as plt

def marr_hildreth_fast(image_path, sigma=1.5, threshold=0.005):
    # 1. Cargar imagen en escala de grises
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print("No se pudo cargar la imagen. Revisa la ruta.")
        return None, None, None, None

    # Convertir a flotante entre 0 y 1
    img_float = img.astype(np.float32) / 255.0

    # 2. Aplicar Laplaciano de Gaussiano (LoG)
    kernel_size = int(2 * np.ceil(3 * sigma) + 1)
    blur = cv2.GaussianBlur(img_float, (kernel_size, kernel_size), sigma)
    log_img = cv2.Laplacian(blur, cv2.CV_32F)

    # 3. Detección de Cruce por Cero VECTORIZADA
    shift_up    = np.roll(log_img, -1, axis=0)
    shift_down  = np.roll(log_img, 1, axis=0)
    shift_left  = np.roll(log_img, -1, axis=1)
    shift_right = np.roll(log_img, 1, axis=1)

    cross_v = (log_img * shift_up < 0) | (log_img * shift_down < 0)
    cross_h = (log_img * shift_left < 0) | (log_img * shift_right < 0)
    zero_crossings = cross_v | cross_h

    kernel_dil = np.ones((3, 3), dtype=np.uint8)
    max_local = cv2.dilate(log_img, kernel_dil)
    min_local = cv2.erode(log_img, kernel_dil)
    edge_strength = max_local - min_local

    thresh_val = threshold * log_img.max()
    
    # El borde final de Marr-Hildreth
    bordes = np.zeros_like(log_img, dtype=np.uint8)
    bordes[(zero_crossings) & (edge_strength > thresh_val)] = 255

    bordes[0:2, :] = 0
    bordes[-2:, :] = 0
    bordes[:, 0:2] = 0
    bordes[:, -2:] = 0

    # =========================================================================
    # NUEVA ETAPA: ELIMINACIÓN DE BORDES MEDIANTE MORFOLOGÍA MATEMÁTICA
    # =========================================================================
    
    # Cambiamos el kernel a (3, 3) para que tenga el tamaño suficiente para 
    # "comerse" los bordes delgados de los frijoles.
    kernel_morf = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    
    # Usamos MORPH_OPEN (Apertura) en lugar de CLOSE. 
    # La apertura realiza una erosión (borra los frijoles) seguida de una dilatación 
    # (recupera el tamaño de las rocas que sobrevivieron).
    bordes_procesados = cv2.morphologyEx(bordes, cv2.MORPH_OPEN, kernel_morf)
    
    return img, log_img, bordes, bordes_procesados

# --- Ejecución ---
ruta_imagen = 'C:\\Users\\Emiliano\\Documents\\ESCOM\\SEMESTRE 4\\PDI\\Proyecto\\beans2.jpg'

# Ejecutamos el algoritmo
original, log_resultado, bordes, bordes_limpios = marr_hildreth_fast(ruta_imagen, sigma=2.0, threshold=0.12)

if bordes is not None:
    # =========================================================================
    # GUARDAR LAS IMÁGENES
    # =========================================================================
    # cv2.imwrite guarda las imágenes en tu disco duro. 
    # Si solo pones el nombre del archivo, se guardará en la misma carpeta 
    # desde donde estás corriendo este script de Python.
    cv2.imwrite('bordes_marr_hildreth.png', bordes)
    cv2.imwrite('bordes_sin_frijoles.png', bordes_limpios)
    print("¡Las imágenes se han guardado exitosamente!")

    # Graficamos 4 subplots para ver la evolución
    plt.figure(figsize=(15, 4))

    plt.subplot(1, 4, 1)
    plt.title("1. Original")
    plt.imshow(original, cmap='gray')
    plt.axis('off')

    plt.subplot(1, 4, 2)
    plt.title("2. LoG")
    plt.imshow(log_resultado, cmap='jet')
    plt.axis('off')

    plt.subplot(1, 4, 3)
    plt.title("3. Bordes Marr-Hildreth")
    plt.imshow(bordes, cmap='gray')
    plt.axis('off')

    plt.subplot(1, 4, 4)
    plt.title("4. Bordes Eliminados (Apertura)")
    plt.imshow(bordes_limpios, cmap='gray')
    plt.axis('off')

    plt.tight_layout()
    plt.show()