import cv2
import numpy as np
import matplotlib.pyplot as plt

def segmentar_rescate_final(image_path):
    # 1. Cargar y espacios de color
    image = cv2.imread(image_path)
    if image is None:
        print("Error al cargar la imagen.")
        return

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 2. Segmentación Base (Para objetos separados)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # OTSU sigue siendo lo mejor con buena iluminación
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Limpieza de ruido
    kernel = np.ones((5, 5), np.uint8)
    thresh_cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
    # Cerramos huecos (por si hay brillos en el frijol)
    thresh_cleaned = cv2.morphologyEx(thresh_cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)

    # 3. HSV para Color y Brillo
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]

    # Encontrar contornos
    contours, _ = cv2.findContours(thresh_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    resultado = image_rgb.copy()
    f_count = 0
    p_count = 0

    print("--- Calibración (Viendo valores de objetos) ---")

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 80: continue # Ignorar ruido

        # --- A. FORMA (Solidez) ---
        hull = cv2.convexHull(cnt)
        area_hull = cv2.contourArea(hull)
        if area_hull == 0: continue
        solidez = float(area) / area_hull

        # --- B. COLOR (HSV promedio) ---
        mask_cnt = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(mask_cnt, [cnt], -1, 255, -1)
        mean_saturation = cv2.mean(s_channel, mask=mask_cnt)[0]
        mean_value = cv2.mean(v_channel, mask=mask_cnt)[0]

        # Imprime los valores para calibración rápida
        # print(f"Objeto: Area {area:.0f} | Solidez {solidez:.2f} | Sat {mean_saturation:.0f} | Val {mean_value:.0f}")

        # --- C. CLASIFICADOR (Ajustado para objetos separados) ---
        
        # Regla 1 (Forma): Si es irregular/terrón -> Piedra (Rojo)
        # Bajé la exigencia a 0.85 para perdonar frijoles "feos"
        if solidez < 0.85:
            es_piedra = True
        else:
            # Regla 2 (Color): Validamos color si es redondito
            if mean_saturation > 35.0: 
                es_piedra = False # Color vivo -> Bayo/Peruano (Verde)
            # Regla 3 (Brillo): Validamos frijoles negros
            # Subí el límite a 100 porque tu foto es muy oscura
            elif mean_value < 100.0: 
                es_piedra = False # Color deslavado y muy oscuro -> Frijol Negro (Verde)
            else:
                es_piedra = True  # Color deslavado y claro/gris -> Piedra lisa (Rojo)

        M = cv2.moments(cnt)
        cx = int(M["m10"] / M["m00"]) if M["m00"] != 0 else 0
        cy = int(M["m01"] / M["m00"]) if M["m00"] != 0 else 0

        if es_piedra:
            cv2.drawContours(resultado, [cnt], -1, (255, 0, 0), 4)
            cv2.putText(resultado, "P", (cx - 15, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            p_count += 1
        else:
            cv2.drawContours(resultado, [cnt], -1, (0, 255, 0), 4)
            cv2.putText(resultado, "F", (cx - 15, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            f_count += 1

    print(f"Total -> Frijoles: {f_count} | Piedras: {p_count}")

    plt.figure(figsize=(10, 8))
    plt.title("Clasificación de Rescate Final (Objetos Separados)")
    plt.imshow(resultado)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# EJECUTA TU IMAGEN AQUÍ
segmentar_rescate_final('img/valio5.jpg')
