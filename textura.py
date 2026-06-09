import cv2
import numpy as np
import matplotlib.pyplot as plt

# 1. Cargar la imagen original a color y en escala de grises
ruta_imagen = 'C:\\Users\\Emiliano\\Documents\\ESCOM\\SEMESTRE 4\\PDI\\Proyecto\\beans.jpg'
img_color = cv2.imread(ruta_imagen)
img_gray = cv2.imread(ruta_imagen, cv2.IMREAD_GRAYSCALE)

if img_color is None:
    print("Error: No se pudo cargar la imagen. Revisa la ruta.")
else:
    # 2. Resaltar la TEXTURA de toda la imagen usando el Laplaciano
    # Usamos CV_32F para no perder los gradientes negativos
    laplacian = cv2.Laplacian(img_gray, cv2.CV_32F)
    # Sacamos el valor absoluto para medir la "fuerza" de la textura
    laplacian_abs = np.absolute(laplacian)

    # 3. Segmentar los objetos usando la Umbralización de Otsu (que ya dominas)
    blur = cv2.GaussianBlur(img_gray, (5, 5), 0)
    _, mascara_binaria = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 4. Encontrar los contornos de todos los objetos en la escena
    contornos, _ = cv2.findContours(mascara_binaria, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Creamos copias para dibujar los resultados visuales
    resultado_frijoles = img_color.copy()
    resultado_piedras = img_color.copy()

    # =========================================================================
    # UMBRAL DE TEXTURA (Ajustable)
    # Si un objeto tiene una desviación estándar mayor a esto, se considera piedra.
    # Tip: Imprime los valores en consola la primera vez para calibrarlo perfectamente.
    # =========================================================================
    UMBRAL_TEXTURA = 12.0  

    for i, c in enumerate(contornos):
        # Filtrar ruidos extremadamente chicos (menores a 50 píxeles)
        if cv2.contourArea(c) < 50:
            continue

        # A. Crear una máscara negra exclusiva para el objeto actual
        mascara_objeto = np.zeros_like(img_gray)
        cv2.drawContours(mascara_objeto, [c], -1, 255, -1) # Rellenamos el objeto de blanco

        # B. CALCULAR TEXTURA: Medimos la desviación estándar del Laplaciano SÓLO dentro del objeto
        _, stddev = cv2.meanStdDev(laplacian_abs, mask=mascara_objeto)
        valor_textura = stddev[0][0]

        # C. CLASIFICACIÓN
        if valor_textura < UMBRAL_TEXTURA:
            # TEXTURA SUAVE -> Es un frijol. Pintamos su contorno de VERDE
            cv2.drawContours(resultado_frijoles, [c], -1, (0, 255, 0), 2)
            # En la imagen de piedras, borramos el frijol pintándolo de negro
            cv2.drawContours(resultado_piedras, [c], -1, (0, 0, 0), -1)
        else:
            # TEXTURA RUGOSA -> Es una piedra. Pintamos su contorno de ROJO
            cv2.drawContours(resultado_frijoles, [c], -1, (0, 0, 255), 2)
            # En la imagen de frijoles limpios, borramos la piedra pintándola de blanco (o fondo)
            cv2.drawContours(resultado_frijoles, [c], -1, (255, 255, 255), -1)

    # 5. Guardar los resultados limpios en tu disco duro
    cv2.imwrite('solo_frijoles_textura.png', resultado_frijoles)
    print("¡Procesamiento por textura terminado con éxito!")

    # =========================================================================
    # MOSTRAR RESULTADOS
    # =========================================================================
    plt.figure(figsize=(15, 5))

    # Convertir BGR a RGB para Matplotlib
    lap_mostrar = cv2.normalize(laplacian_abs, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    plt.subplot(1, 3, 1)
    plt.title("1. Mapa de Textura (Laplaciano)")
    plt.imshow(lap_mostrar, cmap='jet')
    plt.axis('off')

    plt.subplot(1, 3, 2)
    plt.title("2. Clasificación (Verde=Frijol, Rojo=Piedra)")
    plt.imshow(cv2.cvtColor(img_color, cv2.COLOR_BGR2RGB))
    # Superponemos los contornos para el reporte
    for c in contornos:
        if cv2.contourArea(c) > 50:
            _, std = cv2.meanStdDev(laplacian_abs, mask=mascara_objeto)
            color = (0, 255, 0) if cv2.meanStdDev(laplacian_abs, mask=np.zeros_like(img_gray))[1][0][0] < UMBRAL_TEXTURA else (255, 0, 0)
    plt.imshow(cv2.cvtColor(resultado_frijoles, cv2.COLOR_BGR2RGB))
    plt.axis('off')

    plt.subplot(1, 3, 3)
    plt.title("3. Imagen Limpia (Sin Piedras)")
    plt.imshow(cv2.cvtColor(resultado_frijoles, cv2.COLOR_BGR2RGB))
    plt.axis('off')

    plt.tight_layout()
    plt.show()