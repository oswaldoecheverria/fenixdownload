"""
Interfaz de Usuario de Terminal (TUI) Interactiva y HUD en Vivo.
Soporta YouTube, TikTok, Instagram, Twitter/X, Facebook, Twitch, Vimeo y webs multimedia.
Dispone de monitor HUD dinámico de 1 sola línea con alternancia interactiva con tecla [D].
"""

import os
import sys
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import humanize
import questionary
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live

from fenixdownload.extractor import inspect_url
from fenixdownload.downloader import DownloadManager
from fenixdownload.ffmpeg_locator import ensure_ffmpeg_in_path, verify_ffmpeg

console = Console()

# Intentar importar msvcrt para Windows
try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False


def show_banner():
    banner_text = Text()
    banner_text.append("⚡ FENIXDOWNLOAD CLI ⚡\n", style="bold cyan")
    banner_text.append("Acelerador Multi-Hilo Universal • Motor Anti-Bot • MP4 / MP3 Estricto\n", style="bold white")
    banner_text.append("YouTube • TikTok • Instagram • Twitter/X • Facebook • Twitch • Vimeo • DASH/HLS\n", style="dim green")
    banner_text.append("Desarrollado por / Built by Oswaldo Echeverría", style="italic yellow")

    panel = Panel(
        banner_text,
        border_style="cyan",
        subtitle="[bold yellow]Alternativa Libre y Abierta a Internet Download Manager (IDM)[/bold yellow]",
        padding=(1, 2),
    )
    console.print(panel)


def display_media_card(info: Dict[str, Any]):
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="bold cyan", width=18)
    table.add_column("Value", style="white")

    table.add_row("🎬 Fichero / Título:", info.get("title", "Desconocido"))
    table.add_row("🌐 Plataforma:", str(info.get("platform", "Web / Directo")))
    table.add_row("👤 Canal / Autor:", str(info.get("uploader", "Desconocido")))
    table.add_row("⏱️ Duración:", str(info.get("duration", "Desconocida")))
    table.add_row("🔗 Enlace:", str(info.get("url", "")))

    card = Panel(
        table,
        title="[bold green]✓ Ficha Multimedia Detectada[/bold green]",
        border_style="green",
        padding=(0, 1),
    )
    console.print(card)


def format_seconds(seconds: Optional[int | float]) -> str:
    if seconds is None or seconds < 0:
        return "--:--"
    secs = int(seconds)
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def generate_bar(percentage: float, width: int = 28) -> str:
    """Genera una barra de progreso suave de ancho fijo."""
    clamped = max(0.0, min(100.0, percentage))
    filled_len = int(round(width * clamped / 100))
    bar = "█" * filled_len + "░" * (width - filled_len)
    return f"[bold cyan]{bar}[/bold cyan]"


class DownloadHUD:
    """Gestor de visualización HUD dinámica con soporte de alternancia de vista."""

    def __init__(self, title: str, platform: str, format_label: str, threads: int):
        self.title = title
        self.platform = platform
        self.format_label = format_label
        self.threads = threads

        self.percent = 0.0
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.speed = 0.0
        self.eta = None
        self.status_msg = "Conectando e iniciando conexiones paralelas..."
        self.detailed_view = False
        self._running = True

    def toggle_view(self):
        self.detailed_view = not self.detailed_view

    def update_from_hook(self, d: Dict[str, Any]):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            self.downloaded_bytes = downloaded
            self.total_bytes = total
            if total > 0:
                self.percent = (downloaded / total) * 100.0
            self.speed = d.get("speed") or 0.0
            self.eta = d.get("eta")

            frag_idx = d.get("fragment_index")
            frag_cnt = d.get("fragment_count")
            if frag_idx and frag_cnt:
                self.status_msg = f"Fragmentos {frag_idx}/{frag_cnt}"
            else:
                self.status_msg = "Descargando fragmentos concurrentes"
        elif status == "finished":
            self.percent = 100.0
            self.status_msg = "Finalizando / Ensamblando en disco..."

    def render(self):
        total_str = humanize.naturalsize(self.total_bytes, binary=True) if self.total_bytes > 0 else "Calculando..."
        dl_str = humanize.naturalsize(self.downloaded_bytes, binary=True)
        speed_str = f"{humanize.naturalsize(self.speed, binary=True)}/s" if self.speed > 0 else "--/s"
        eta_str = format_seconds(self.eta)
        bar = generate_bar(self.percent, width=28)

        if not self.detailed_view:
            # Vista 1: Modo Compacto de 1 sola línea dinámica + mensaje de reanudación
            line1 = (
                f"[bold cyan]⚡ [{self.threads} Hilos][/bold cyan] {bar} "
                f"[bold white]{self.percent:>5.1f}%[/bold white] • "
                f"[dim]{dl_str}/{total_str}[/dim] • "
                f"[bold green]🚀 {speed_str}[/bold green] • "
                f"[yellow]⏱️ {eta_str}[/yellow] • "
                f"[cyan][{self.status_msg}][/cyan]"
            )
            line2 = (
                f"[dim yellow]💡 Reanudación activa: Si se interrumpe (Ctrl+C), repite el comando y continuará desde el {self.percent:.1f}%.[/dim yellow]  "
                f"[bold cyan][Presiona D para detalles][/bold cyan]"
            )
            return Group(Text.from_markup(line1), Text.from_markup(line2))
        else:
            # Vista 2: Modo Dashboard Completo (Al presionar D)
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("K", style="bold cyan", width=18)
            table.add_column("V", style="white")

            table.add_row("🎬 Fichero:", self.title[:55] + "..." if len(self.title) > 55 else self.title)
            table.add_row("🌐 Origen y Formato:", f"{self.platform}  •  {self.format_label}  •  {self.threads} Conexiones Paralelas")
            table.add_row("📊 Progreso:", f"{bar}  [bold white]{self.percent:.1f}%[/bold white]")
            table.add_row("📦 Transferencia:", f"{dl_str} / {total_str}  •  Velocidad: [bold green]🚀 {speed_str}[/bold green]  •  ETA: [yellow]⏱️ {eta_str}[/yellow]")
            table.add_row("⚡ Estado de Red:", f"[cyan]{self.status_msg} (Hilos #1 - #{self.threads} activos)[/cyan]")
            table.add_row("🎮 Control de Teclado:", "[bold cyan][D][/bold cyan] Volver a vista compacta  •  [bold yellow][Ctrl+C][/bold yellow] Pausar descarga")
            table.add_row("💡 Reanudación:", f"Todo byte está seguro en disco. Continuará desde el {self.percent:.1f}% al reiniciar.")

            panel = Panel(
                table,
                title="[bold cyan]⚡ Dashboard de Descarga Acelerada (IDM Turbo)[/bold cyan]",
                border_style="cyan",
                padding=(0, 1),
            )
            return panel


def run_interactive():
    show_banner()

    ffmpeg_dir = ensure_ffmpeg_in_path()
    if not ffmpeg_dir or not verify_ffmpeg(ffmpeg_dir):
        console.print("[yellow]⚠️ Aviso: FFmpeg no fue detectado en PATH. Algunas funciones de conversión podrían limitarse.[/yellow]")
    else:
        console.print(f"[dim green]✓ Motor FFmpeg & FFprobe activo:[/dim green] [dim]{ffmpeg_dir}[/dim]\n")

    # 1. Solicitar URL
    url = questionary.text(
        "Pega la URL del video a descargar (YouTube, TikTok, Instagram, Twitter/X, Facebook, Twitch, etc.):",
        validate=lambda text: True if text.strip().startswith(("http://", "https://")) else "Ingresa una URL válida (ej. https://...)",
    ).ask()

    if not url:
        console.print("[red]Operación cancelada por el usuario.[/red]")
        return

    # 2. Inspección Sigilosa
    with console.status("[bold cyan]🔍 Analizando enlace con cabeceras sigilosas anti-bloqueo...", spinner="dots"):
        try:
            info = inspect_url(url.strip(), ffmpeg_path=ffmpeg_dir)
        except Exception as e:
            console.print(f"\n[bold red]❌ Error al inspeccionar enlace:[/bold red] {e}")
            return

    console.print()
    display_media_card(info)
    console.print()

    # 3. Tipo de Descarga: MP4 o MP3
    format_choice = questionary.select(
        "¿En qué formato deseas obtener el archivo?",
        choices=[
            questionary.Choice("🎬 Video Completo (Forzado a .MP4)", value="video"),
            questionary.Choice("🎵 Solo Audio (Extracción a .MP3)", value="audio"),
        ],
    ).ask()

    if not format_choice:
        return

    # 4. Calidad
    selected_quality = "best"
    if format_choice == "video":
        video_choices = [
            questionary.Choice(opt["label"], value=opt["value"])
            for opt in info.get("video_options", [])
        ]
        if video_choices:
            selected_quality = questionary.select(
                "Selecciona la resolución deseada para el MP4:",
                choices=video_choices,
            ).ask()
    else:
        audio_choices = [
            questionary.Choice(opt["label"], value=opt["value"])
            for opt in info.get("audio_options", [])
        ]
        if audio_choices:
            selected_quality = questionary.select(
                "Selecciona la fidelidad de compresión para el MP3:",
                choices=audio_choices,
            ).ask()

    if not selected_quality:
        return

    # 5. Aceleración Multi-Hilo (Estilo IDM)
    threads_choice = questionary.select(
        "Nivel de aceleración multi-conexión (Descarga paralela):",
        choices=[
            questionary.Choice("⚡ 8 Hilos Concurrentes (Recomendado - Máxima velocidad y estabilidad)", value=8),
            questionary.Choice("🚀 16 Hilos Concurrentes (Turbo IDM - Saturation)", value=16),
            questionary.Choice("🛡️ 4 Hilos Concurrentes (Modo Conservador / Redes sensibles)", value=4),
        ],
    ).ask()

    if not threads_choice:
        threads_choice = 8

    # 6. Carpeta de destino
    default_dir = Path(__file__).resolve().parent.parent.parent / "downloads"
    dest_dir = questionary.text(
        "Carpeta de destino de las descargas:",
        default=str(default_dir),
    ).ask()

    if not dest_dir:
        dest_dir = str(default_dir)

    console.print()

    # 7. Iniciar HUD Dinámico y Descarga
    format_label_str = "MP4 (Video)" if format_choice == "video" else "MP3 (Audio)"
    hud = DownloadHUD(
        title=info.get("title", "Video"),
        platform=info.get("platform", "Web"),
        format_label=format_label_str,
        threads=threads_choice,
    )

    # Hilo para escuchar pulsaciones de teclado [D] en Windows
    def key_listener():
        while hud._running:
            if HAS_MSVCRT and msvcrt.kbhit():
                try:
                    ch = msvcrt.getch()
                    if ch in (b"d", b"D"):
                        hud.toggle_view()
                except Exception:
                    pass
            time.sleep(0.1)

    key_thread = threading.Thread(target=key_listener, daemon=True)
    key_thread.start()

    download_target_url = url.strip()

    with Live(hud.render(), console=console, refresh_per_second=4, transient=False) as live:
        def on_progress(d: Dict[str, Any]):
            hud.update_from_hook(d)
            live.update(hud.render())

        downloader = DownloadManager(
            output_dir=dest_dir,
            concurrency=threads_choice,
            progress_callback=on_progress,
        )

        try:
            if format_choice == "video":
                out_path = downloader.download_video(download_target_url, quality=selected_quality)
            else:
                out_path = downloader.download_audio(download_target_url, bitrate=selected_quality)

            hud.percent = 100.0
            hud.status_msg = "Completado con éxito"
            live.update(hud.render())
        except Exception as e:
            hud._running = False
            console.print(f"\n[bold red]❌ Error durante la descarga:[/bold red] {e}")
            return
        finally:
            hud._running = False

    console.print()
    success_panel = Panel(
        Text.from_markup(
            f"[bold green]¡Descarga y conversión finalizadas con éxito![/bold green]\n\n"
            f"📁 [bold white]Ubicación:[/bold white] [cyan]{dest_dir}[/cyan]\n"
            f"🎬 [bold white]Formato Final:[/bold white] [yellow]{format_label_str}[/yellow]\n"
            f"⚡ [bold white]Hilos utilizados:[/bold white] {threads_choice}\n"
            f"🛡️ [bold white]Modo:[/bold white] Conexión sigilosa / Anti-bot activo"
        ),
        title="[bold green]✓ Descarga Lista[/bold green]",
        border_style="green",
    )
    console.print(success_panel)
