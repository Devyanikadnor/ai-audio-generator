import uuid
from datetime import datetime
import os


def generate_filename(prefix: str = "tts_", ext: str = ".mp3") -> str:
    """
    Generate a unique filename for an audio file.
    Example: tts_20251121_abc12345.mp3
    """
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    rand = uuid.uuid4().hex[:8]
    return f"{prefix}{ts}_{rand}{ext}"


def ensure_dir(path: str) -> None:
    """
    Ensure directory exists.
    """
    os.makedirs(path, exist_ok=True)
