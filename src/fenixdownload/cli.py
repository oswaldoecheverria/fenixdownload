"""
Punto de Entrada Principal de FenixDownload CLI.
Soporta tanto modo interactivo TUI como argumentos directos por línea de comandos.
Desarrollado por Oswaldo Echeverría.
"""

import sys
import argparse
from pathlib import Path

from fenixdownload.tui import run_interactive, console
from fenixdownload.downloader import DownloadManager
from fenixdownload.ffmpeg_locator import ensure_ffmpeg_in_path


def get_default_download_dir() -> str:
    """Retorna la carpeta de descargas relativa al proyecto de forma multiplataforma."""
    return str(Path(__file__).resolve().parent.parent.parent / "downloads")


def main():
    default_downloads = get_default_download_dir()
    parser = argparse.ArgumentParser(
        prog="fenixdownload",
        description="⚡ FENIXDOWNLOAD: Acelerador de descargas multimedia multi-hilo estilo IDM para consola. By Oswaldo Echeverría.",
    )
    parser.add_argument("url", nargs="?", default=None, help="URL del video o medio a descargar")
    parser.add_argument(
        "-f",
        "--format",
        choices=["mp4", "mp3"],
        default="mp4",
        help="Formato final estricto deseado: mp4 (video) o mp3 (audio)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        default="best",
        help="Calidad de video (best, 1080, 720, 480) o bitrate de audio (320, 256, 192, 128)",
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=8,
        help="Número de hilos/conexiones paralelas concurrentes (por defecto 8)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=default_downloads,
        help=f"Directorio de destino para los archivos descargados (por defecto: {default_downloads})",
    )

    args = parser.parse_args()

    # Si no se pasó URL, iniciar el modo TUI interactivo
    if not args.url:
        run_interactive()
        return

    # Modo directo por línea de comandos
    url = args.url.strip()
    console.print(f"[bold cyan]⚡ FenixDownload:[/bold cyan] {url}")
    console.print(f"[dim]Formato: {args.format.upper()} | Calidad: {args.quality} | Hilos: {args.concurrency}[/dim]\n")

    downloader = DownloadManager(
        output_dir=args.output,
        concurrency=args.concurrency,
    )

    try:
        if args.format.lower() == "mp3":
            downloader.download_audio(url, bitrate=args.quality)
        else:
            downloader.download_video(url, quality=args.quality)
        console.print(f"[bold green]✓ Descarga completada en:[/bold green] {args.output}")
    except Exception as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
