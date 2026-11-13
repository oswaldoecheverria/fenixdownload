"""
Módulo de Descarga Acelerada y Conversión Estricta (MP4 / MP3).
Maneja multi-hilos estilo IDM, reanudación byte a byte y conversión garantizada con FFmpeg.
"""

from pathlib import Path
from typing import Dict, Any, Callable, Optional
import yt_dlp

from fenixdownload.stealth import get_yt_dlp_stealth_options
from fenixdownload.ffmpeg_locator import ensure_ffmpeg_in_path


class DownloadManager:
    def __init__(
        self,
        output_dir: str | Path = "downloads",
        concurrency: int = 8,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.concurrency = max(1, min(concurrency, 32))
        self.progress_callback = progress_callback
        self.ffmpeg_dir = ensure_ffmpeg_in_path()

    def _progress_hook(self, d: Dict[str, Any]):
        if self.progress_callback:
            self.progress_callback(d)

    def download_video(
        self,
        url: str,
        quality: str = "best",
        target_filename: Optional[str] = None,
    ) -> str:
        """
        Descarga el video forzando SIEMPRE contenedor MP4 final.
        quality: 'best' o una altura numérica como '1080', '720', '480'.
        """
        outtmpl = str(self.output_dir / (target_filename or "%(title)s [%(id)s].%(ext)s"))

        if quality == "best" or quality == "original":
            format_spec = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        else:
            format_spec = (
                f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={quality}]+bestaudio/"
                f"best[height<={quality}]/best"
            )

        ydl_opts = get_yt_dlp_stealth_options()
        ydl_opts.update({
            "format": format_spec,
            "outtmpl": outtmpl,
            "continuedl": True,  # Reanudación byte a byte
            "concurrent_fragment_downloads": self.concurrency,  # Multi-hilo estilo IDM
            "merge_output_format": "mp4",  # Forzar contenedor MP4
            "postprocessors": [
                {
                    # Asegurar conversión a MP4 si la fuente original fue WebM/MKV
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ],
            "progress_hooks": [self._progress_hook],
            "quiet": True,
            "noprogress": True,
            "no_warnings": True,
        })

        if self.ffmpeg_dir:
            ydl_opts["ffmpeg_location"] = self.ffmpeg_dir

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "video")
            return str(self.output_dir / f"{title}.mp4")

    def download_audio(
        self,
        url: str,
        bitrate: str = "320",
        target_filename: Optional[str] = None,
    ) -> str:
        """
        Descarga y convierte estrictamente a formato MP3 con la tasa de bits indicada.
        """
        outtmpl = str(self.output_dir / (target_filename or "%(title)s [%(id)s].%(ext)s"))

        ydl_opts = get_yt_dlp_stealth_options()
        ydl_opts.update({
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "continuedl": True,  # Reanudación automática
            "concurrent_fragment_downloads": self.concurrency,  # Multi-hilo
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": bitrate,
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ],
            "progress_hooks": [self._progress_hook],
            "quiet": True,
            "noprogress": True,
            "no_warnings": True,
        })

        if self.ffmpeg_dir:
            ydl_opts["ffmpeg_location"] = self.ffmpeg_dir

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "audio")
            return str(self.output_dir / f"{title}.mp3")

    def download_direct_file(
        self,
        url: str,
        filename: Optional[str] = None,
    ) -> str:
        """
        Descarga archivos directos genéricos (TeraBox, zip, documentos) con reanudación y multi-hilo.
        """
        outtmpl = str(self.output_dir / (filename or "%(title)s.%(ext)s"))

        ydl_opts = get_yt_dlp_stealth_options()
        ydl_opts.update({
            "outtmpl": outtmpl,
            "continuedl": True,
            "concurrent_fragment_downloads": self.concurrency,
            "progress_hooks": [self._progress_hook],
            "quiet": True,
            "noprogress": True,
            "no_warnings": True,
        })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return str(self.output_dir / (filename or info.get("title", "archivo")))
