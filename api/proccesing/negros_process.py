import cv2
import numpy as np

def procesar_mi_imagen(imagen_bytes: bytes) -> bytes:
    nparr = np.frombuffer(imagen_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Ejemplo flojo: Volver la imagen a escala de grises
    imagen_procesada = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # -------------------------------------------
    
    # 2. Convertir la matriz de OpenCV de vuelta a bytes (formato PNG o JPEG)
    _, buffer = cv2.imencode('.png', imagen_procesada)
    return buffer.tobytes()