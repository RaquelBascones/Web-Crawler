# Mini Web Crawler con Base de Datos, HTML e IA

Proyecto desarrollado en Python que permite descargar una página web, extraer sus enlaces, generar resúmenes automáticos, guardar los datos en una base de datos SQLite, mostrar los resultados en una página HTML y clasificar la web con un modelo básico de inteligencia artificial.

---

## Índice

1. Descripción del proyecto  
2. Funcionalidades  
3. Estructura del proyecto  
4. Requisitos  
5. Instalación de dependencias  
6. Ejecución del programa  
7. Resultados  
8. Clasificación mediante inteligencia artificial  
9. Observaciones  

---

## 1. Descripción del proyecto

Este proyecto implementa un mini web crawler capaz de analizar una página web, extraer sus enlaces, obtener el contenido de cada uno de ellos y generar un resumen en español de forma automática. Toda la información se almacena en una base de datos SQLite y se muestra en una vista HTML generada automáticamente. Además, se incluye un sistema básico de clasificación del contenido mediante inteligencia artificial.

---

## 2. Funcionalidades

- Descarga de páginas web mediante la librería requests.  
- Extracción de enlaces usando expresiones regulares.  
- Obtención del texto real de cada página mediante trafilatura.  
- Generación automática de resúmenes.  
- Traducción automática de los resúmenes al español.  
- Almacenamiento de la información en una base de datos SQLite.  
- Generación automática de un archivo HTML con los resultados.  
- Clasificación del contenido mediante un modelo de inteligencia artificial.  

---

## 3. Estructura del proyecto
- SuperNenasPEC3.py
- crawler.db
- supernenas.html
---

## 4. Requisitos

Es necesario tener instalado:

- Python 3.9 o superior.  
- Librerías:
  - requests  
  - trafilatura  
  - googletrans  
  - scikit-learn  

---

## 5. Instalación de dependencias

