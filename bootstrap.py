"""
FenixDownload CLI - Asistente de Arranque Autónomo y Auto-Instalación (Zero-Configuration).
Funciona exclusivamente con la biblioteca estándar de Python para garantizar ejecución en cualquier sistema.
Desarrollado por Oswaldo Echeverría.
"""

import os
import sys
import platform
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
MARKER_FILE = PROJECT_ROOT / ".setup_done"
BIN_DIR = PROJECT_ROOT / "bin"
VENV_DIR = PROJECT_ROOT / ".venv"


def get_platform_info() -> tuple[str, str]:
    """Retorna el sistema operativo legible y la arquitectura."""
    system = platform.system()
    arch = platform.machine()
    if system == "Windows":
        return f"Windows ({arch})", "windows"
    elif system == "Linux":
        return f"Linux ({arch})", "linux"
    elif system == "Darwin":
        return f"macOS ({arch})", "macos"
    return f"{system} ({arch})", "unknown"


def check_ffmpeg_exists() -> bool:
    """Verifica si ffmpeg está disponible en PATH o en bin local."""
    if shutil.which("ffmpeg"):
        return True
    local_exe = BIN_DIR / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    return local_exe.exists()


def check_python_dependencies() -> bool:
    """Verifica si las librerías esenciales están instaladas en el entorno."""
    try:
        # Si existe venv, comprobar si tiene los módulos requeridos
        if os.name == "nt":
            py_exe = VENV_DIR / "Scripts" / "python.exe"
        else:
            py_exe = VENV_DIR / "bin" / "python"

        if py_exe.exists():
            cmd = [str(py_exe), "-c", "import yt_dlp, rich, questionary, httpx"]
            res = subprocess.run(cmd, capture_output=True)
            return res.returncode == 0
        else:
            import yt_dlp
            import rich
            import questionary
            import httpx
            return True
    except Exception:
        return False


def install_python_deps() -> bool:
    """Instala las dependencias usando uv si existe o python -m pip."""
    print("  -> Configurando entorno virtual y paquetes...")

    # Intentar con uv primero (ultrarrápido)
    if shutil.which("uv"):
        try:
            res = subprocess.run(["uv", "sync"], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
            if res.returncode == 0:
                return True
        except Exception:
            pass

    # Fallback con python estándar
    try:
        # Crear venv si no existe
        if not VENV_DIR.exists():
            subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True, capture_output=True)

        if os.name == "nt":
            pip_exe = VENV_DIR / "Scripts" / "pip.exe"
        else:
            pip_exe = VENV_DIR / "bin" / "pip"

        reqs = ["yt-dlp>=2026.10.26", "rich>=15.0.0", "questionary>=2.1.1", "httpx>=0.28.1", "humanize>=4.17.0", "fake-useragent>=2.2.0"]
        cmd = [str(pip_exe), "install", "--upgrade", "pip"] + reqs
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0
    except Exception as e:
        print(f"     [!] Error instalando dependencias: {e}")
        return False


def install_ffmpeg_windows() -> bool:
    """Descarga e instala una copia portátil de FFmpeg para Windows en bin/."""
    print("  -> Descargando motor portátil FFmpeg para Windows...")
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = BIN_DIR / "ffmpeg.zip"

    # URL ligera y confiable de release essentials
    url = "https://github.com/GyanD/codexffmpeg/releases/download/9.0.1/ffmpeg-9.0.1-essentials_build.zip"

    try:
        def reporthook(count, block_size, total_size):
            if total_size > 0:
                percent = min(100, int(count * block_size * 100 / total_size))
                print(f"\r     Descargando FFmpeg: {percent}%", end="", flush=True)

        urllib.request.urlretrieve(url, zip_path, reporthook)
        print("\n     Extrayendo binarios...")

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.namelist():
                if member.endswith("ffmpeg.exe") or member.endswith("ffprobe.exe"):
                    filename = Path(member).name
                    target = BIN_DIR / filename
                    with zip_ref.open(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)

        if zip_path.exists():
            zip_path.unlink()

        return (BIN_DIR / "ffmpeg.exe").exists()
    except Exception as e:
        print(f"\n     [!] Error descargando FFmpeg automático: {e}")
        # Intentar winget como fallback
        if shutil.which("winget"):
            print("     Intentando instalación alternativa vía winget...")
            w_res = subprocess.run(["winget", "install", "Gyan.FFmpeg.Essentials", "--accept-package-agreements", "--accept-source-agreements"], capture_output=True)
            return w_res.returncode == 0
        return False


def install_ffmpeg_linux() -> bool:
    """Detecta gestor de paquetes de Linux e intenta instalar ffmpeg."""
    print("  -> Detectando gestor de paquetes de Linux para FFmpeg...")
    pkg_managers = [
        ("apt-get", ["sudo", "apt-get", "update"], ["sudo", "apt-get", "install", "-y", "ffmpeg"]),
        ("pacman", [], ["sudo", "pacman", "-S", "--noconfirm", "ffmpeg"]),
        ("dnf", [], ["sudo", "dnf", "install", "-y", "ffmpeg"]),
        ("zypper", [], ["sudo", "zypper", "install", "-y", "ffmpeg"]),
    ]

    for name, update_cmd, install_cmd in pkg_managers:
        if shutil.which(name):
            try:
                print(f"     Ejecutando instalación mediante {name}...")
                if update_cmd:
                    subprocess.run(update_cmd, check=False)
                res = subprocess.run(install_cmd, check=True)
                return res.returncode == 0
            except Exception:
                pass

    print("     [!] Por favor instala ffmpeg con el gestor de tu distribución (ej. sudo apt install ffmpeg).")
    return False


def install_ffmpeg_macos() -> bool:
    """Instala ffmpeg en macOS mediante Homebrew."""
    print("  -> Instalando FFmpeg mediante Homebrew en macOS...")
    if shutil.which("brew"):
        try:
            res = subprocess.run(["brew", "install", "ffmpeg"], check=True)
            return res.returncode == 0
        except Exception:
            pass
    print("     [!] Por favor instala Homebrew o ejecuta: brew install ffmpeg")
    return False


def run_first_time_wizard(os_type: str, os_name: str) -> bool:
    """Muestra el asistente interactivo de primera ejecución."""
    print("=" * 72)
    print("  ⚡ FENIXDOWNLOAD CLI - Asistente de Configuración Inicial ⚡")
    print("  Desarrollado por Oswaldo Echeverría")
    print("=" * 72)
    print(f"\n[i] Detectamos que es la primera vez que ejecutas FenixDownload en este equipo.")
    print(f"    Sistema detectado: {os_name}\n")
    print("FenixDownload necesita preparar dos componentes esenciales:")
    print("  1. Entorno de ejecución y dependencias multimedia (yt-dlp, rich, etc.)")
    print("  2. Motor de multiplexado y conversión FFmpeg (para MP4 y MP3)\n")

    confirm = input("¿Deseas que FenixDownload instale y configure todo automáticamente ahora? [S/n]: ").strip().lower()
    if confirm in ("n", "no"):
        print("\n[!] Instalación cancelada. Puedes instalar los requisitos manualmente siguiendo el README.md.")
        return False

    print("\nIniciando preparación del sistema...\n")

    # 1. Dependencias de Python
    print("[1/3] Verificando dependencias de Python...")
    if not check_python_dependencies():
        if not install_python_deps():
            print("     [!] No se pudieron instalar todas las dependencias. Continuando...")
        else:
            print("     [OK] Dependencias de Python listas.")
    else:
        print("     [OK] Dependencias de Python ya instaladas.")

    # 2. FFmpeg
    print("[2/3] Verificando motor multimedia FFmpeg...")
    if not check_ffmpeg_exists():
        if os_type == "windows":
            ff_ok = install_ffmpeg_windows()
        elif os_type == "linux":
            ff_ok = install_ffmpeg_linux()
        elif os_type == "macos":
            ff_ok = install_ffmpeg_macos()
        else:
            ff_ok = False

        if ff_ok:
            print("     [OK] Motor FFmpeg configurado con éxito.")
        else:
            print("     [!] Aviso: No se pudo auto-instalar FFmpeg. Asegúrate de instalarlo en tu sistema.")
    else:
        print("     [OK] Motor FFmpeg detectado correctamente.")

    # 3. Verificación final y guardado de estado
    print("[3/3] Corroborando integridad final...")
    MARKER_FILE.write_text("setup_complete=true\n", encoding="utf-8")
    print("     [OK] Sistema verificado.")

    print("\n✓ ¡Configuración completada con éxito!")
    print("=" * 72 + "\n")
    return True


def ensure_ready_and_run():
    """Punto de entrada del bootstrapper."""
    os_name, os_type = get_platform_info()

    # Si es la primera vez o falta el marcador, correr el asistente
    is_ready = MARKER_FILE.exists() and check_ffmpeg_exists() and check_python_dependencies()

    if not is_ready:
        success = run_first_time_wizard(os_type, os_name)
        if not success:
            sys.exit(1)

    # Ejecutar la aplicación principal usando el intérprete de venv si existe
    if os.name == "nt":
        py_exe = VENV_DIR / "Scripts" / "python.exe"
    else:
        py_exe = VENV_DIR / "bin" / "python"

    target_py = str(py_exe) if py_exe.exists() else sys.executable

    # Invocar fenixdownload.cli con los argumentos recibidos
    cmd = [target_py, "-m", "fenixdownload.cli"] + sys.argv[1:]
    sys.exit(subprocess.call(cmd, cwd=str(PROJECT_ROOT)))


if __name__ == "__main__":
    ensure_ready_and_run()
