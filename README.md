# Mi Cerebro Digital (CPP)

**Tu vida, conectada y resumida de manera totalmente gratuita.**


## 📖 Introducción

**Mi Cerebro Digital** es un proyecto de **Cloud Personal Privado (CPP)** nacido como respuesta a la pérdida de soberanía digital[cite: 222]. [cite_start]En lugar de ceder nuestros datos a grandes corporaciones, hemos diseñado una infraestructura auto-alojada (*self-hosted*) que centraliza, protege y procesa la información personal en el hogar.

El sistema integra fotos, documentos y datos de salud en una interfaz unificada, utilizando **Inteligencia Artificial Local** para generar resúmenes narrativos de tu día a día, garantizando que tus datos nunca salgan de tu red privada.

## 🚀 Objetivos del Proyecto

* **Soberanía de Datos:** Alojamiento físico de la información en una Raspberry Pi 5, eliminando intermediarios.
* **Privacidad Absoluta:** Uso de VPN (WireGuard) y procesamiento de IA en el borde (*Edge Computing*), sin enviar datos a la nube pública.
* **Agregación de Datos:** Unificación de fuentes heterogéneas:
    * 📸 Fotos y Vídeos (Immich).
    * 📄 Documentos (Paperless-ngx).
    * ❤️ Salud (Health Connect: Pasos y Sueño).
    * 🗓️ Agenda (Nextcloud Calendar: Eventos y Citas).
    * 🗺️ Ubicación (Leaflet.js: Rutas y Lugares Visitados).
* **Narrativa con IA:** Implementación de un LLM local para convertir metadatos fríos en historias coherentes sobre tu día.

## 🛠️ Arquitectura y Tecnologías

El proyecto utiliza una arquitectura de microservicios contenerizados sobre hardware de bajo consumo optimizado para alto rendimiento I/O.

![Arquitectura del Sistema](ruta/a/tu/diagrama_arquitectura.png)

### Infraestructura
* **Hardware:** Raspberry Pi 5 (8GB RAM) con arranque desde SSD vía USB 3.0 para evitar cuellos de botella.
* **OS:** Raspberry Pi OS Lite (64-bit).
* **Orquestación:** Docker & Docker Compose, gestionado visualmente con **Portainer**.
* **Red y Seguridad:** Túnel VPN **WireGuard** para acceso remoto y autenticación SSH mediante claves RSA.

### Backend y Servicios de Datos
* **Immich:** Gestión de fotos con reconocimiento facial y mapas de calor.
* **Paperless-ngx:** Digitalización de documentos con OCR (Tesseract).
* **Nginx:** Servidor web ligero para el despliegue del dashboard.
* **Middleware:** Scripts personalizados en Python/Node.js para la ingesta y normalización de datos.

### Inteligencia Artificial (Local)
* **Motor:** Ollama ejecutándose en la Raspberry Pi.
* **Modelo:** Phi-3 (o similar cuantizado) optimizado para hardware limitado.
* **Enfoque:** La IA procesa un CSV estructurado (ubicaciones, fechas, salud, ...) para generar texto narrativo.

### Frontend
* **Tecnologías:** HTML5, Tailwind CSS y JavaScript Vanilla (sin frameworks pesados para maximizar rendimiento).
* **Visualización:** Mapas interactivos con **Leaflet.js** para mostrar rutas basadas en las fotos del día.

## 📸 Galería de Funcionalidades

### 1. Panel de Control y Resumen IA
El usuario selecciona una fecha y el sistema genera una narrativa contando qué hizo, basándose en sus fotos, ubicación y salud.

![Generación de Resumen con IA](ruta/a/tu/captura_resumen_ia.png)

### 2. Gestión de Contenedores
Monitorización en tiempo real del estado de los servicios (Immich, Postgres, Redis, etc.) mediante Portainer.

![Portainer Dashboard](ruta/a/tu/captura_portainer.png)

### 3. Servicios Auto-alojados (Immich y Paperless)
Integración completa de herramientas profesionales para la gestión de activos digitales.

![Interfaz de Immich y Paperless](ruta/a/tu/captura_servicios.png)

## 🔄 El Desafío Técnico: Pivote de la IA

Durante el desarrollo (Fase PT4), nos enfrentamos a una limitación crítica: el uso de IA multimodal para "ver" y analizar píxeles de imágenes saturaba la CPU y RAM de la Raspberry Pi, provocando caídas del sistema.

**Nuestra Solución:**
Cambiamos el paradigma de **"Ver imágenes"** a **"Leer datos"**.
En lugar de procesar imágenes pesadas, desarrollamos un middleware que extrae metadatos (EXIF, coordenadas, contadores de pasos) y se los alimenta a la IA en formato JSON[cite: 298, 299]. [cite_start]Esto permitió generar resúmenes precisos con una latencia aceptable y sin comprometer la estabilidad del servidor.

## 🔮 Futuro del Proyecto

* **Voz a Texto:** Implementación de Whisper local para añadir notas de voz subjetivas al resumen diario.
* **Hardware NPU:** Integración de aceleradores como Coral Edge TPU para reducir tiempos de inferencia.
* **RAG (Retrieval-Augmented Generation):** Dotar a la IA de memoria a largo plazo mediante bases de datos vectoriales.

## 👥 Autores - Grupo 4

Este proyecto ha sido desarrollado como parte de la asignatura PTI (2025) por:

* **Iago Díaz Lamas** - Coordinador y Backend.
* **Enrique de Vicente-Tutor Castillo** - Infraestructura y Redes.
* **Xavi Pascual Closa** - Servicios de Datos.
* **Darío González Paniego** - Integración e IA.
