import cv2
import numpy as np

def segmentar_frijoles_y_piedras(ruta_imagen):
    # Cargar la imagen original
    imagen = cv2.imread(ruta_imagen)
    imagen_resultados = imagen.copy()
    
    # ---------------------------------------------------------
    # PASO 1: "Limpiar los lentes" (Suavizado)
    # ---------------------------------------------------------
    gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    # Filtro de mediana para quitar basuritas sin borrar bordes
    gris_suavizado = cv2.medianBlur(gris, 7)
    
    # ---------------------------------------------------------
    # PASO 2: "Barrer todo junto" (Umbralización y Relleno)
    # ---------------------------------------------------------
    _, mascara = cv2.threshold(gris_suavizado, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # --- Paso 2.1: "Resanar los baches" (Rellenar reflejos de luz) ---
    contornos_huecos, _ = cv2.findContours(mascara, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contornos_huecos:
        cv2.drawContours(mascara, [cnt], 0, 255, -1)

    # ---------------------------------------------------------
    # PASO 3: "Levantar muros fronterizos" (Watershed para separar)
    # ---------------------------------------------------------
    kernel = np.ones((3,3), np.uint8)
    fondo_seguro = cv2.dilate(mascara, kernel, iterations=2)

    # Transformada de distancia (buscar los picos de las montañas)
    dist_transform = cv2.distanceTransform(mascara, cv2.DIST_L2, 5)
    
    # ¡Ajuste clave!: Exigimos que el pico esté al 70% de altura para no fusionar frijoles
    _, picos_seguros = cv2.threshold(dist_transform, 0.8 * dist_transform.max(), 255, 0)
    picos_seguros = np.uint8(picos_seguros)

    zona_desconocida = cv2.subtract(fondo_seguro, picos_seguros)

    _, marcadores = cv2.connectedComponents(picos_seguros)
    marcadores = marcadores + 1
    marcadores[zona_desconocida == 255] = 0 

    img_color = cv2.cvtColor(gris_suavizado, cv2.COLOR_GRAY2BGR)
    marcadores = cv2.watershed(img_color, marcadores)

    # Dibujar las fronteras separadoras en nuestra máscara (líneas negras)
    mascara[marcadores == -1] = 0
    
    # *Nota: Eliminamos la erosión aquí para no "morder" pedazos de frijoles válidos.

    # ---------------------------------------------------------
    # PASO 4: Encontrar los objetos individuales listos
    # ---------------------------------------------------------
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    frijoles = []
    piedras = []
    
    for contorno in contornos:
        area = cv2.contourArea(contorno)
        
        # Ignorar basuritas minúsculas
        if area < 100:
            continue
            
        # ---------------------------------------------------------
        # PASO 5: "Tocar a ciegas" (Calcular la Forma / Solidez)
        # ---------------------------------------------------------
        hull = cv2.convexHull(contorno)
        area_hull = cv2.contourArea(hull)
        
        if area_hull == 0:
            continue
            
        solidez = float(area) / area_hull
        
        # ---------------------------------------------------------
        # PASO 6: "Pasar el dedo y Pesar" (Textura y Tono)
        # ---------------------------------------------------------
        mascara_objeto = np.zeros(gris.shape, dtype=np.uint8)
        cv2.drawContours(mascara_objeto, [contorno], -1, 255, -1)
        
        mean, stddev = cv2.meanStdDev(gris, mask=mascara_objeto)
        
        tono_promedio = mean[0][0]
        textura_rugosidad = stddev[0][0]
        
        # ---------------------------------------------------------
        # PASO 7: El Clasificador Mejorado
        # ---------------------------------------------------------
        # Las tres reglas de seguridad para ser considerado un frijol:
        es_redondo = solidez > 0.90
        es_liso = textura_rugosidad < 25.0
        es_tono_correcto = 180 < tono_promedio < 190 # Evita piedras blancas o carbón
        
        if es_redondo and es_liso and es_tono_correcto:
            frijoles.append(contorno)
        else:
            piedras.append(contorno)

    # ---------------------------------------------------------
    # Visualización de Resultados (Ventanas Ajustables)
    # ---------------------------------------------------------
    cv2.drawContours(imagen_resultados, frijoles, -1, (0, 255, 0), 2)
    cv2.drawContours(imagen_resultados, piedras, -1, (0, 0, 255), 2)
    
    print(f"Total encontrados -> Frijoles: {len(frijoles)}, Piedras: {len(piedras)}")
    
    # Crear ventanas ajustables (Como un proyector)
    cv2.namedWindow("Mascara (Separacion)", cv2.WINDOW_NORMAL)
    cv2.namedWindow("Clasificacion Final", cv2.WINDOW_NORMAL)
    
    # Definir el tamaño máximo para que quepan en tu pantalla
    cv2.resizeWindow("Mascara (Separacion)", 800, 600)
    cv2.resizeWindow("Clasificacion Final", 800, 600)
    
    cv2.imshow("Mascara (Separacion)", mascara)
    cv2.imshow("Clasificacion Final", imagen_resultados)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# ---------------------------------------------------------
# Ejecución
# ---------------------------------------------------------
# Reemplaza 'ruta_de_tu_imagen.jpg' con el nombre real de tu archivo
segmentar_frijoles_y_piedras('img/beans4.jpg')