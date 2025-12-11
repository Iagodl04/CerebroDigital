# Mi Cerebro Digital (CPP)

**Tu vida, conectada y resumida de manera totalmente gratuita.**


## 📖 Introducción

En la actualidad, nos enfrentamos a una elección forzada: ceder nuestra privacidad a grandes corporaciones tecnológicas o renunciar a la comodidad de la nube. **Mi Cerebro Digital** nace como una respuesta ética y técnica a este dilema, proponiendo un Cloud Personal Privado (CPP) donde la soberanía de los datos es absoluta.

Más allá de un simple sistema de copias de seguridad, este proyecto transforma el almacenamiento pasivo en una memoria activa. Mediante una infraestructura auto-alojada físicamente en el hogar y un motor de Inteligencia Artificial Local, el sistema unifica tus fotos, documentos y métricas de salud para narrar la historia de tu día a día. Todo ello garantizando que tu información más íntima nunca salga de tu propia red.

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

![Diagrama de Flujo de Tecnologías](flujoPTI.png)

### Infraestructura
* **Hardware:** Raspberry Pi 5 (8GB RAM) con arranque desde SSD vía USB 3.0 para evitar cuellos de botella.
* **OS:** Raspberry Pi OS Lite (64-bit).
* **Orquestación:** Docker & Docker Compose, gestionado visualmente con **Portainer**.
* **Red y Seguridad:** Túnel VPN **WireGuard** para acceso remoto y autenticación SSH.

### Backend y Servicios de Datos
* **Immich:** Gestión de fotos con reconocimiento facial y mapas de calor.
* **Paperless-ngx:** Digitalización, OCR e indexado de documentos.
* **Nginx:** Servidor web ligero para el despliegue del dashboard.
* **Middleware:** Scripts personalizados en Python/Node.js para la ingesta y normalización de datos.

### Inteligencia Artificial (Local)
* **Motor:** Ollama ejecutándose en la Raspberry Pi.
* **Modelo:** Qwen 2.5 (1.5B), un modelo ligero y optimizado para hardware limitado.
* **Enfoque:** La IA procesa un CSV estructurado (ubicaciones, fechas, salud, ...) para generar texto narrativo.

### Frontend
* **Tecnologías:** HTML5, Tailwind CSS y JavaScript Vanilla (sin frameworks pesados para maximizar rendimiento).
* **Visualización:** Mapas interactivos con **Leaflet.js** para mostrar rutas basadas en las fotos del día.

## 📸 Galería de Funcionalidades

### 1. Panel de Control y Resumen IA
El usuario selecciona una fecha y el sistema genera una narrativa contando qué hizo, basándose en sus fotos, ubicación y salud.

![Generación de Resumen con IA](resumen_ia.png)

### 2. Gestión de Contenedores
Monitorización en tiempo real del estado de los servicios (Immich, Postgres, Redis, etc.) mediante Portainer.

![Portainer Dashboard](portainer.png)

### 3. Servicios Auto-alojados (Immich, Paperless y NextCloud)
Integración completa de herramientas profesionales para la gestión de activos digitales.

![Interfaz de Immich](immich.png)
![Interfaz de Paperless](paperless.png)
![Interfaz de NextCloud](nextcloud.png)

## 🔄 El Desafío Técnico: Pivote de la IA

Durante el desarrollo (Fase PT4), nos enfrentamos a una limitación crítica: el uso de IA multimodal para "ver" y analizar píxeles de imágenes saturaba la CPU y RAM de la Raspberry Pi, provocando caídas del sistema.

**Nuestra Solución:**
Cambiamos el paradigma de **"Ver imágenes"** a **"Leer datos"**.
En lugar de procesar imágenes pesadas, desarrollamos un middleware que extrae metadatos (EXIF, coordenadas, contadores de pasos) y se los alimenta a la IA en formato CSV. Esto permitió generar resúmenes precisos con una latencia aceptable y sin comprometer la estabilidad del servidor.

## 🔮 Futuro del Proyecto: Evolución del Hardware

Aunque la implementación actual en Raspberry Pi valida el concepto, el futuro de **Mi Cerebro Digital** pasa por romper las barreras físicas del hardware actual. Para lograr una experiencia fluida con modelos de IA más complejos y múltiples usuarios simultáneos, proponemos una evolución hacia plataformas más robustas.

El objetivo es migrar de un entorno de desarrollo (PoC) a una infraestructura de producción capaz de manejar cargas de trabajo intensivas mediante tres vías de mejora:

### 1. Potencia Bruta y Memoria (Arquitectura x86)
La limitación principal actual es la memoria RAM (max 8GB en RPi). Migrar a una arquitectura de PC tradicional permitiría:
* **Más RAM:** Escalar a 32GB o 64GB, permitiendo cargar modelos de lenguaje (LLMs) mucho más grandes y precisos en memoria, junto con bases de datos pesadas en paralelo.
* **Almacenamiento NVMe:** Uso de discos nativos en placa base para velocidades de lectura/escritura muy superiores al USB 3.0 actual.
* **Hardware sugerido:** *Intel NUC, Mini-PCs (Beelink/Lenovo Tiny) o Servidores domésticos.*

### 2. Especialización en Inteligencia Artificial (Edge AI)
Para que la IA responda en tiempo real (milisegundos en lugar de segundos) y pueda analizar vídeo en vivo, es necesario hardware dedicado al cálculo tensorial:
* **GPUs y NPUs:** Abandonar el uso de la CPU para la IA y delegar el trabajo a núcleos gráficos o unidades de procesamiento neuronal.
* **Hardware sugerido:**
    * **Ecosistema NVIDIA Jetson (Nano/Orin):** Placas de desarrollo con núcleos CUDA diseñados específicamente para robótica e IA autónoma.
    * **Aceleradores USB:** Dispositivos como Coral Edge TPU o Hailo AI que se conectan al servidor existente para "turboalimentar" la inferencia.

### 3. Seguridad y Redundancia de Datos
Para garantizar que "Tu Cerebro Digital" sea eterno y resistente a fallos físicos:
* **Sistemas RAID:** Implementación de matrices de discos redundantes (RAID 1 o RAID 5). Si un disco duro físico se rompe, los datos sobreviven en los otros sin interrupción del servicio.
* **Hardware sugerido:** *Integración con NAS comerciales (Synology/QNAP) o construcción de un servidor con múltiples bahías de disco.*

## 👥 Autores - Grupo 4

Este proyecto ha sido desarrollado como parte de la asignatura PTI (2025) por:

* **Iago Díaz Lamas** 
* **Enrique de Vicente-Tutor Castillo** 
* **Xavi Pascual Closa** 
* **Darío González Paniego**
