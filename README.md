# 🌾 Clasificador y Limpiador de Granos mediante Procesamiento Digital de Imágenes (PDI)

¡Holi! Bienvenido a este proyecto desarrollado para la materia de **Procesamiento Digital de Imágenes** (4to Semestre - ESCOM). El objetivo principal de este sistema es automatizar el control de calidad en muestras de granos (frijoles), logrando aislar los elementos orgánicos y eliminar por completo impurezas comunes como piedras, rocas y residuos texturizados.

---

## 🚀 ¿Qué hace nuestro trabajo?

Este software implementa un pipeline completo de visión artificial que toma una fotografía analógica/digital de muestras de frijoles mezclados con piedras y realiza las siguientes tareas:
1. **Detección Avanzada de Bordes:** Identifica con alta precisión matemática los contornos de los objetos mediante operadores clásicos y direccionales.
2. **Segmentación Inteligente:** Aplica umbralización automática adaptable al entorno de iluminación.
3. **Filtro Morfológico Dinámico:** Limpia el ruido estático, rellena huecos internos y conecta contornos utilizando operaciones de alta potencia (*Opening* y *Closing*).
4. **Discriminación por Análisis de Textura:** Separa los frijoles de las piedras analizando la rugosidad superficial (varianza de frecuencias altas), permitiendo que el algoritmo funcione de manera universal sin importar el color o tamaño del grano.

---

## 🛠️ Algoritmos Clave Implementados

El núcleo del proyecto se basa en la comparación e implementación de dos de los detectores de bordes más potentes del PDI:

### 1. Detector de Bordes de Marr-Hildreth (Laplaciano de Gaussiano)
Este algoritmo encuentra los bordes emulando el sistema visual humano a través de dos fases principales:
* **Suavizado:** Un filtro Gaussiano reduce el ruido de alta frecuencia controlado por un parámetro $\sigma$.
* **Evolución:** Se calcula el Laplaciano ($\nabla^2$) y se buscan de forma **vectorizada y optimizada** los *Cruces por Cero* (Zero-Crossings). Esto genera bordes delgados, precisos y omnidireccionales de un solo píxel de grosor.

### 2. Operador de Bordes de Kirsch (Detector Direccional)
A diferencia de los filtros comunes, Kirsch es un operador de brújula (*compass*). Utiliza **8 máscaras de convolución diferentes** rotadas a $45^\circ$:

| Norte | Noreste | Este | Sureste |
|:---:|:---:|:---:|:---:|
| $k_1$ | $k_8$ | $k_7$ | $k_6$ |

El algoritmo aplica las 8 máscaras sobre cada píxel y conserva la **respuesta máxima**, lo que lo hace idóneo para detectar texturas complejas, orientaciones críticas y geometrías angulares (como las de las rocas).

---

## 🧠 El Toque Maestro: Filtrado Universal por Textura

> **El Reto:** Un frijol negro pequeño puede medir lo mismo que una piedra mediana, haciendo que el filtrado por tamaño falle.
> 
> **La Solución:** Implementamos un análisis de textura local. Calculamos el valor absoluto del Laplaciano y medimos la **Desviación Estándar (`cv2.meanStdDev`)** de manera individual por objeto. 

* **Frijoles (Superficie lisa):** Transiciones tonales suaves $\rightarrow$ Desviación estándar baja.
* **Piedras (Superficie rugosa/porosa):** Micro-bordes constantes $\rightarrow$ Desviación estándar alta $\rightarrow$ **¡Eliminadas mediante máscaras invertidas y operaciones `Bitwise AND`!**

---

## 📋 Requisitos del Sistema

Para ejecutar este proyecto necesitas tener instalado Python 3.x junto con las siguientes librerías:

```bash
pip install opencv-python numpy matplotlib
