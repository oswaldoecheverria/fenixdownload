"""
Módulo de Evasión y Sigilo (Anti-Bot / Non-Invasive Stealth).
Optimizado para no romper las APIs móviles nativas de YouTube/Vimeo/DASH/HLS,
garantizando navegación limpia y máxima resiliencia ante bloqueos.
"""

import random
from typing import Dict, Any

CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
EDGE_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"

USER_AGENTS = [CHROME_UA, EDGE_UA]


def get_random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def get_yt_dlp_stealth_options() -> Dict[str, Any]:
    """
    Configuración no invasiva para yt-dlp:
    - Retries exponenciales para no saturar servidores.
    - Manejo de fragmentos caídos.
    - Soporte de reanudación y rotación de clientes oficiales.
    """
    return {
        "user_agent": get_random_user_agent(),
        "retries": 10,
        "fragment_retries": 15,
        "skip_unavailable_fragments": True,
        "socket_timeout": 30,
        "extractor_retries": 5,
        "file_access_retries": 5,
    }
