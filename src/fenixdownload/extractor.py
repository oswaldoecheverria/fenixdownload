"""
Módulo Extractor de Medios Universal.
Inspecciona URLs de YouTube, TikTok, Instagram, Twitter/X, Facebook, Twitch, Vimeo y webs multimedia.
"""

from typing import Dict, Any, List, Optional
import urllib.parse
import humanize
import yt_dlp

from fenixdownload.stealth import get_yt_dlp_stealth_options


def format_duration(seconds: Optional[int | float]) -> str:
    """Convierte segundos a formato hh:mm:ss o mm:ss."""
    if not seconds:
        return "Desconocida"
    secs = int(seconds)
    hours = secs // 3600
    minutes = (secs % 3600) // 60
    remaining_secs = secs % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{remaining_secs:02d}"
    return f"{minutes:02d}:{remaining_secs:02d}"


def detect_platform(url: str, extractor_name: Optional[str] = None) -> str:
    """Identifica el nombre comercial de la plataforma."""
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube"
    if "tiktok.com" in url_lower:
        return "TikTok"
    if "instagram.com" in url_lower:
        return "Instagram"
    if "facebook.com" in url_lower or "fb.watch" in url_lower:
        return "Facebook"
    if "twitter.com" in url_lower or "x.com" in url_lower:
        return "Twitter / X"
    if "twitch.tv" in url_lower:
        return "Twitch"
    if "vimeo.com" in url_lower:
        return "Vimeo"

    if extractor_name:
        return extractor_name.capitalize()

    try:
        domain = urllib.parse.urlparse(url).netloc
        return domain.replace("www.", "")
    except Exception:
        return "Web Streaming"


def inspect_url(url: str, ffmpeg_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Inspecciona cualquier enlace multimedia web o de redes sociales.
    Retorna la ficha técnica completa y opciones de formato y calidad.
    """
    clean_url = url.strip()

    ydl_opts = get_yt_dlp_stealth_options()
    ydl_opts.update({
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    })
    if ffmpeg_path:
        ydl_opts["ffmpeg_location"] = ffmpeg_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(clean_url, download=False)
        if not info:
            raise ValueError("No se pudo extraer información del enlace proporcionado.")

    title = info.get("title", "Video sin título")
    duration = format_duration(info.get("duration"))
    platform = detect_platform(clean_url, info.get("extractor"))
    uploader = info.get("uploader") or info.get("channel") or platform
    thumbnail = info.get("thumbnail")
    description = info.get("description", "")
    if description and len(description) > 120:
        description = description[:117] + "..."

    formats = info.get("formats", [])

    # Agrupar calidades de video únicas
    video_qualities: Dict[int, Dict[str, Any]] = {}
    best_audio_size = 0

    # Buscar tamaño del mejor audio para sumar al video si vienen separados (DASH)
    for f in formats:
        if f.get("vcodec") == "none" and f.get("acodec") != "none":
            size = f.get("filesize") or f.get("filesize_approx") or 0
            if size > best_audio_size:
                best_audio_size = size

    for f in formats:
        height = f.get("height")
        vcodec = f.get("vcodec")
        if not height or vcodec == "none":
            continue

        size = f.get("filesize") or f.get("filesize_approx") or 0
        if f.get("acodec") == "none" and size > 0:
            size += best_audio_size

        if height not in video_qualities or size > (video_qualities[height].get("size") or 0):
            video_qualities[height] = {
                "height": height,
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "fps": f.get("fps"),
                "size": size,
                "size_str": humanize.naturalsize(size, binary=True) if size > 0 else "Dinámico / HLS",
            }

    sorted_heights = sorted(video_qualities.keys(), reverse=True)
    video_options: List[Dict[str, Any]] = []

    # Opción automática recomendada
    video_options.append({
        "label": f"⭐ Mejor Calidad Disponible (MP4 Original {platform})",
        "value": "best",
        "height": 9999,
        "size_str": "Máxima resolución posible",
    })

    resolution_labels = {
        4320: "8K UHD",
        2160: "4K UHD",
        1440: "2K QHD",
        1080: "Full HD 1080p",
        720: "HD 720p",
        480: "SD 480p",
        360: "360p (Ahorro de datos)",
        240: "240p (Baja resolución)",
        144: "144p (Mínima)",
    }

    if sorted_heights:
        for h in sorted_heights:
            q = video_qualities[h]
            tag = resolution_labels.get(h, f"{h}p")
            fps_tag = f" @ {q['fps']}fps" if q.get("fps") and q["fps"] > 30 else ""
            label = f"{tag}{fps_tag} — [{q['size_str']}]"
            video_options.append({
                "label": label,
                "value": str(h),
                "height": h,
                "size_str": q["size_str"],
            })
    else:
        # Plataformas con flujos únicos (TikTok / Reels)
        approx_size = info.get("filesize") or info.get("filesize_approx") or 0
        size_str = humanize.naturalsize(approx_size, binary=True) if approx_size > 0 else "Auto"
        video_options.append({
            "label": f"Calidad Estándar / Reels [{size_str}]",
            "value": "best",
            "height": 1080,
            "size_str": size_str,
        })

    # Opciones de audio MP3
    audio_options = [
        {"label": "⭐ Máxima Fidelidad (MP3 320 kbps CBR)", "value": "320"},
        {"label": "Alta Fidelidad (MP3 256 kbps VBR)", "value": "256"},
        {"label": "Estándar Equilibrado (MP3 192 kbps VBR)", "value": "192"},
        {"label": "Ligero / Podcasts (MP3 128 kbps CBR)", "value": "128"},
    ]

    return {
        "title": title,
        "duration": duration,
        "uploader": uploader,
        "platform": platform,
        "thumbnail": thumbnail,
        "description": description,
        "url": clean_url,
        "video_options": video_options,
        "audio_options": audio_options,
    }
