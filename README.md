<div align="center">

# ⚡ FenixDownload CLI
### *Acelerador de Descargas Multimedia Multi-Hilo Universal • Alternativa Libre a IDM*

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-success)](#-compatibilidad-multiplataforma)
[![Speed](https://img.shields.io/badge/Engine-Multi--Thread%20Segmented-brightgreen)](#-c%C3%B3mo-funciona-la-aceleraci%C3%B3n-multi-hilo)

**Desarrollado con ❤️ por [Oswaldo Echeverría](https://github.com/oswaldoecheverria)**

*Una herramienta de consola moderna, ligera, no invasiva y de código abierto para descargar video y audio a máxima velocidad desde más de 1.800 sitios web.*

---

</div>

## 📌 Tabla de Contenidos
1. [¿Por qué FenixDownload? (vs. Internet Download Manager)](#-por-qu%C3%A9-fenixdownload-vs-internet-download-manager)
2. [Características Principales](#-caracter%C3%ADsticas-principales)
3. [Arquitectura del Sistema](#-arquitectura-del-sistema)
4. [Compatibilidad Multiplataforma](#-compatibilidad-multiplataforma)
5. [Instalación Rápida](#-instalaci%C3%B3n-r%C3%A1pida)
6. [Guía de Uso](#-gu%C3%ADa-de-uso)
   - [Modo Interactivo (TUI)](#1-modo-interactivo-tui-recomendado)
   - [Modo Línea de Comandos (CLI / Scripts)](#2-modo-directo-por-l%C3%ADnea-de-comandos)
7. [Tecnologías Utilizadas](#-tecnolog%C3%ADas-utilizadas)
8. [Cómo Contribuir](#-c%C3%B3mo-contribuir)
9. [Licencia](#-licencia)

---

## 🥊 ¿Por qué FenixDownload? (vs. Internet Download Manager)

Durante años, **Internet Download Manager (IDM)** fue el referente para acelerar descargas en Windows. Sin embargo, en la web moderna presenta limitaciones críticas:

| Característica | Internet Download Manager (IDM) | ⚡ FenixDownload CLI |
| :--- | :--- | :--- |
| **Licencia y Costo** | De pago / Propietario / Licencias de prueba | **100% Libre y de Código Abierto (MIT)** |
| **Sistemas Operativos** | Exclusivo de Windows | **Windows, Linux y macOS** |
| **Plataformas Modernas (YouTube, TikTok, Reels)** | Falla frecuentemente al unir streams DASH separados | **Soporte nativo impecable (+1.800 sitios)** |
| **Entrega de Formato** | Descarga formatos crudos (.ts, .webm, audio mudo) | **Conversión estricta garantizada a MP4 o MP3** |
| **Consumo de Recursos** | Instala drivers de red invasivos y extensiones | **Sin drivers invasivos ni capturas de paquetes** |
| **Automatización** | Difícil de integrar en scripts o servidores | **Totalmente operable por consola y scripts** |
| **Interfaz de Usuario** | Ventana emergente clásica con anuncios | **HUD dinámico en vivo en 1 sola línea con tecla `[D]`** |

---

## 🚀 Características Principales

- **⚡ Aceleración Multi-Hilo Segmentada:** Divide archivos y fragmentos en hasta **16 o 32 conexiones paralelas concurrentes**, saturando el ancho de banda y superando las restricciones de velocidad por conexión única de los servidores.
- **🔄 Reanudación Byte a Byte:** Si tu red se corta o detienes la descarga con `Ctrl+C`, el progreso queda a salvo en disco. Vuelve a ejecutar la descarga y continuará exactamente en el último byte transferido.
- **🛡️ Motor Sigiloso Anti-Bot (Stealth Mode):** Emula la huella digital y cabeceras de navegadores modernos reales (Chrome y Edge en Windows), mitigando bloqueos por WAF, Akamai o Cloudflare.
- **🎬 Entrega Estricta en MP4:** Sin importar si el video original está en WebM, MKV o flujos DASH/HLS fragmentados, FenixDownload los une o remuxa al instante en un contenedor estándar **`.mp4`**.
- **🎵 Extracción de Audio a MP3:** Descarga únicamente la pista sonora y la codifica a **`.mp3`** con la tasa de bits deseada (320 kbps de máxima fidelidad, 256, 192 o 128 kbps), incrustando metadatos automáticamente.
- **🖥️ Monitor HUD Dinámico de 1 Línea:** Sin parpadeos ni líneas repetitivas en la consola. Muestra porcentaje, barra gráfica fluida, velocidad (`MB/s`) y tiempo restante (ETA).
- **🎮 Alternancia en Tiempo Real (`Tecla [D]`):** Puedes presionar la tecla **`D`** durante cualquier descarga para expandir el panel completo con el detalle de todos los hilos o volver a la vista compacta.

---

## 🏗️ Arquitectura del Sistema

```text
                               ┌─────────────────────────┐
                               │     URL del Usuario     │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │  Extractor Sigiloso     │
                               │  (Anti-Bot / yt-dlp)    │
                               └────────────┬────────────┘
                                            │ Inspección de flujos y calidades
                                            ▼
                               ┌─────────────────────────┐
                               │   Menú TUI Interactivo   │
                               │   (Formato, Hilos, Dir) │
                               └────────────┬────────────┘
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
       ┌─────────────────────────┐                     ┌─────────────────────────┐
       │ Flujos DASH / HLS       │                     │ Descargas Directas HTTP │
       │ (Video y Audio sep.)    │                     │ (Multi-conexión Range)  │
       └────────────┬────────────┘                     └────────────┬────────────┘
                    │                                               │
                    └───────────────────────┬───────────────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │ Motor de Descarga       │
                               │ Paralela (8 a 32 hilos) │
                               └────────────┬────────────┘
                                            │ Reanudación y Ensamblado
                                            ▼
                               ┌─────────────────────────┐
                               │ Motor FFmpeg Multiplex  │
                               │ Remux instantáneo a MP4 │
                               │ o transcodificación MP3 │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │ Archivo Final Optimizado│
                               │ en carpeta downloads/   │
                               └─────────────────────────┘
```

---

## 💻 Compatibilidad Multiplataforma

FenixDownload utiliza rutas relativas dinámicas (`pathlib`) y APIs POSIX estándar, haciéndolo compatible de forma nativa con:

- 🪟 **Windows 10 / 11** (PowerShell, CMD, Windows Terminal)
- 🐧 **Linux** (Ubuntu, Debian, Fedora, Arch, Alpine, etc.)
- 🍎 **macOS** (Apple Silicon M1/M2/M3 y procesadores Intel)

---

## 📦 Instalación Rápida

### Requisitos Previos
1. **Python 3.12+** instalado.
2. **FFmpeg** instalado en tu sistema:
   - **Windows:** `winget install Gyan.FFmpeg.Essentials`
   - **Linux:** `sudo apt install ffmpeg` o `sudo pacman -S ffmpeg`
   - **macOS:** `brew install ffmpeg`
3. *(Opcional recomendado)* **uv** para gestión ultrarrápida: `pip install uv`

### Clonar el Repositorio
```bash
git clone https://github.com/oswaldoecheverria/fenixdownload.git
cd fenixdownload
```

### Instalar Dependencias
Si usas `uv`:
```bash
uv sync
```
O con `pip` tradicional:
```bash
pip install -e .
```

---

## 🕹️ Guía de Uso

### 1. Modo Interactivo TUI (Recomendado)

Inicia el asistente gráfico por consola:

**En Windows:**
```powershell
.\fenixdownload.ps1
# o desde CMD / doble clic:
.\fenixdownload.bat
```

**En Linux / macOS:**
```bash
chmod +x fenixdownload.sh
./fenixdownload.sh
```

El programa te guiará paso a paso:
1. Pega la URL del video.
2. Se analizarán las calidades reales disponibles.
3. Elige si deseas **MP4 (Video)** o **MP3 (Audio)**.
4. Selecciona la resolución (4K, 1080p, 720p...) o tasa de bits de audio.
5. Elige el número de conexiones (4, 8 o 16 hilos).
6. Disfruta de la descarga acelerada con la barra dinámica HUD. Durante la descarga:
   - Presiona **`D`** para ver el panel de hilos.
   - Presiona **`D`** nuevamente para volver a la línea compacta.

---

### 2. Modo Directo por Línea de Comandos

Ideal para descargas rápidas o scripts automatizados:

```bash
# Descargar video en máxima calidad forzando MP4 con 8 hilos:
fenixdownload "https://www.youtube.com/watch?v=..." -f mp4

# Descargar video de Twitter/X o Instagram en MP4:
fenixdownload "https://x.com/..." -f mp4

# Descargar video de TikTok en 1080p con 16 hilos turbo:
fenixdownload "https://www.tiktok.com/@user/video/..." -f mp4 -q 1080 -c 16

# Extraer audio a MP3 de máxima fidelidad (320 kbps):
fenixdownload "https://www.youtube.com/watch?v=..." -f mp3 -q 320

# Guardar en una carpeta personalizada:
fenixdownload "https://..." -o "/ruta/a/mis/videos"
```

---

## ⚙️ Tecnologías Utilizadas

- **[Python 3.12+](https://www.python.org/):** Base del lenguaje.
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp):** Motor universal de extracción y decodificación de flujos.
- **[FFmpeg](https://ffmpeg.org/):** Motor de multiplexado y conversión ultra rápida sin pérdida de calidad.
- **[Rich](https://github.com/Textualize/rich):** Renderizado de terminal, paneles, tablas y barra HUD en vivo.
- **[Questionary](https://github.com/tmbo/questionary):** Menús interactivos con selección por teclado.
- **[HTTPX](https://github.com/encode/httpx):** Cliente HTTP moderno para inspección de red.

---

## 🤝 Cómo Contribuir

¡Las contribuciones de la comunidad son bienvenidas! Si deseas agregar nuevas funciones, mejorar la velocidad o reportar fallos:

1. Haz un **Fork** de este repositorio.
2. Crea una rama para tu función (`git checkout -b feature/nueva-mejora`).
3. Realiza tus cambios y haz commit (`git commit -m 'feat: agrega nueva funcionalidad'`).
4. Haz push a tu rama (`git push origin feature/nueva-mejora`).
5. Abre un **Pull Request** explicando tus mejoras.

---

## 📄 Licencia

Este proyecto está bajo la Licencia **MIT**. Consulta el archivo [LICENSE](file:///F:/proyectos/fenixdownload/LICENSE) para más detalles.

---

<div align="center">

**¿Te sirvió el proyecto? ¡Déjale una ⭐ en GitHub!**  
Creado con dedicación por **Oswaldo Echeverría**

</div>
