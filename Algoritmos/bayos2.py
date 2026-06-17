import cv2
import numpy as np

def filtrar_por_area(mascara_binaria, area_minima=110):
    """
    Filtro Geométrico: Analiza cada objeto blanco en la imagen binaria.
    Si su área en píxeles es menor que 'area_minima', lo borra (lo pinta de negro).
    """
    # Encontrar todos los objetos independientes
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mascara_binaria, connectivity=8)
    
    # Crear una máscara vacía para poner solo lo limpio
    mascara_limpia = np.zeros_like(mascara_binaria)
    
    # El índice 0 es el fondo, empezamos desde el 1
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= area_minima:
            mascara_limpia[labels == i] = 255
            
    return mascara_limpia


def separar_y_descargar_binarios(ruta_imagen):
# 1. Cargar y redimensionar la imagen
    imagen = cv2.imread(ruta_imagen)
    
    if imagen is None:
        print("Error: No se pudo cargar la imagen.")
        return

    escala = 1.0
    ancho = int(imagen.shape[1] * escala)
    alto = int(imagen.shape[0] * escala)
    imagen = cv2.resize(imagen, (ancho, alto))

    # Convertir a espacio de color HSV
    hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
    
    # ---------------------------------------------------------
    # PASO EXTRA: FILTRO DE ILUMINACIÓN (Elimina esquinas oscuras y sombras)
    # ---------------------------------------------------------
    # Separamos los canales H, S y V
    h, s, v = cv2.split(hsv)
    
    # Creamos un mapa difuminado gigante del brillo para capturar solo el degradado de la luz
    mapa_luz = cv2.GaussianBlur(v, (101, 101), 0)
    
    # Dividimos el brillo original entre el mapa de luz para homogeneizar toda la hoja a blanco
    v_corregido = cv2.divide(v, mapa_luz, scale=255)
    
    # Volvemos a fusionar los canales con el brillo ya corregido
    hsv = cv2.merge([h, s, v_corregido])
    
    # ---------------------------------------------------------
    # PASO 1: MÁSCARA BINARIA DE FRIJOLES
    # ---------------------------------------------------------
    rango_bajo_frijol = np.array([10, 110, 50])
    rango_alto_frijol = np.array([35, 255, 255])
    mascara_frijoles = cv2.inRange(hsv, rango_bajo_frijol, rango_alto_frijol)
    
    kernel = np.ones((5,5), np.uint8)
    mascara_frijoles = cv2.morphologyEx(mascara_frijoles, cv2.MORPH_OPEN, kernel)
    mascara_frijoles = cv2.morphologyEx(mascara_frijoles, cv2.MORPH_CLOSE, kernel)

    # ---------------------------------------------------------
    # PASO 2: MÁSCARA BINARIA DE TODOS LOS OBJETOS (Fondo invertido)
    # ---------------------------------------------------------
    # Como la luz ya es uniforme, el fondo de papel es un blanco casi perfecto.
    # Podemos usar un rango de brillo alto y estable (de 200 a 255).
    rango_bajo_fondo = np.array([0, 0, 200]) 
    rango_alto_fondo = np.array([180, 40, 255])
    mascara_fondo = cv2.inRange(hsv, rango_bajo_fondo, rango_alto_fondo)
    
    # Invertimos para que los objetos queden en blanco (255) y el papel en negro (0)
    mascara_objetos = cv2.bitwise_not(mascara_fondo)
    
    kernel_grande = np.ones((20,20), np.uint8) #20x20 para las fotos de Diego, 7x7 para rocas
    mascara_objetos = cv2.morphologyEx(mascara_objetos, cv2.MORPH_OPEN, kernel_grande)

    # ---------------------------------------------------------
    # PASO 3: RESTA DE MÁSCARAS PARA EXTRAER SOLO LAS PIEDRAS
    # ---------------------------------------------------------
    # El XOR fallaba porque los bordes de "objetos" y "frijoles" no coinciden
    # pixel a pixel (distintos kernels/operaciones), dejando "medias lunas".
    #
    # Solución: dilatamos la máscara de frijoles para que cubra también
    # su borde/sombra, y luego restamos eso de la máscara de objetos.
    # Lo que sobreviva son las piedras (y posible ruido pequeño, que
    # se elimina en el filtro de área de abajo).
    kernel_dilatacion = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mascara_objetos = cv2.dilate(mascara_objetos, kernel_dilatacion, iterations=2)
    mascara_objetos = cv2.erode(mascara_objetos, kernel_dilatacion, iterations=2)
    mascara_frijoles_dilatada = cv2.dilate(mascara_frijoles, kernel_dilatacion, iterations=2)

    # Piedras = Objetos AND NOT (Frijoles + su borde dilatado)
    mascara_piedras = cv2.bitwise_and(mascara_objetos, cv2.bitwise_not(mascara_frijoles_dilatada))

    mascara_piedras = cv2.morphologyEx(mascara_piedras, cv2.MORPH_CLOSE, kernel)

    # Apertura para limpiar puntos sueltos / ruido residual
    mascara_piedras = cv2.morphologyEx(mascara_piedras, cv2.MORPH_OPEN, kernel_grande)

    # ---------------------------------------------------------
    # PASO 3.5: EL TOQUE MAESTRO - FILTRADO GEOMÉTRICO DE ÁREA
    # ---------------------------------------------------------
    # Aplicamos el filtro para eliminar manchitas pequeñas que no son piedras

    mascara_frijoles_limpia = filtrar_por_area(mascara_frijoles, area_minima=200)
    mascara_piedras_limpia = filtrar_por_area(mascara_piedras, area_minima=50)

    mascara_piedras_limpia = cv2.dilate(mascara_piedras_limpia, kernel_dilatacion, iterations=2)
    ##mascara_piedras_limpia = cv2.erode(mascara_piedras_limpia, kernel_dilatacion, iterations=2)

    # ---------------------------------------------------------
    # PASO 4: DESCARGAR / GUARDAR IMÁGENES BINARIAS
    # ---------------------------------------------------------
    ruta_salida_frijoles = "img/resultado_binario_frijoles.png"
    ruta_salida_piedras = "img/resultado_binario_piedras.png"
    
    cv2.imwrite(ruta_salida_frijoles, mascara_frijoles_limpia)
    cv2.imwrite(ruta_salida_piedras, mascara_piedras_limpia)
    solo_rocas_color = cv2.bitwise_and(imagen, imagen, mask=mascara_piedras_limpia)

    print("¡Procesamiento exitoso! Archivos guardados en la carpeta 'img/':")
    print(f" -> {ruta_salida_frijoles}")
    print(f" -> {ruta_salida_piedras}")

    # ---------------------------------------------------------
    # PASO 5: MOSTRAR VENTANAS
    # ---------------------------------------------------------
    cv2.imshow('0. Imagen Original', imagen)
    cv2.imshow('0.5. Máscara Frijoles', mascara_objetos)
    cv2.imshow('1. Binario Frijoles (Limpio)', mascara_frijoles_limpia)
    cv2.imshow('2. Binario Piedras (Resta + Filtro)', mascara_piedras_limpia)
    cv2.imshow('3. Piedras a Color', solo_rocas_color)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Ejecutar programa
separar_y_descargar_binarios("img/Frijoles-bayos-piedras-02.jpeg")