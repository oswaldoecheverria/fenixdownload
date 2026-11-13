"""
Localizador y Gestor de FFmpeg y FFprobe.
Detecta si FFmpeg existe en PATH, en rutas comunes de Windows (Winget, Scoop, Choco, Local bin)
o en la carpeta local del proyecto, y registra el directorio en el entorno PATH del proceso.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def find_ffmpeg_dir() -> Optional[str]:
    """Busca y retorna el directorio que contiene ffmpeg.exe y ffprobe.exe."""
    # 1. Comprobar si ya está en PATH
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return str(Path(ffmpeg_in_path).parent)

    # 2. Comprobar carpeta bin local del proyecto
    project_bin = Path(__file__).resolve().parent.parent.parent / "bin"
    if (project_bin / "ffmpeg.exe").exists():
        return str(project_bin)

    # 3. Comprobar rutas típicas de WinGet
    localappdata = os.environ.get("LOCALAPPDATA", "")
    if localappdata:
        winget_links = Path(localappdata) / "Microsoft" / "WinGet" / "Links"
        if (winget_links / "ffmpeg.exe").exists():
            return str(winget_links)

        winget_pkgs = Path(localappdata) / "Microsoft" / "WinGet" / "Packages"
        if winget_pkgs.exists():
            for exe in winget_pkgs.glob("**/ffmpeg.exe"):
                return str(exe.parent)

    # 4. Comprobar Program Files
    for pf in ["C:\\Program Files", "C:\\Program Files (x86)"]:
        pf_path = Path(pf)
        if pf_path.exists():
            for exe in pf_path.glob("**/ffmpeg.exe"):
                return str(exe.parent)

    return None


def find_ffmpeg() -> Optional[str]:
    """Alias de compatibilidad para find_ffmpeg_dir."""
    return find_ffmpeg_dir()


def ensure_ffmpeg_in_path() -> Optional[str]:
    """Añade el directorio de FFmpeg al PATH del proceso actual para máxima compatibilidad."""
    ff_dir = find_ffmpeg_dir()
    if ff_dir:
        current_path = os.environ.get("PATH", "")
        if ff_dir not in current_path:
            os.environ["PATH"] = f"{ff_dir}{os.path.pathsep}{current_path}"
    return ff_dir


def verify_ffmpeg(ff_dir: str) -> bool:
    """Verifica que el ejecutable responda correctamente."""
    try:
        exe = Path(ff_dir) / "ffmpeg.exe" if os.name == "nt" else Path(ff_dir) / "ffmpeg"
        res = subprocess.run([str(exe), "-version"], capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False
