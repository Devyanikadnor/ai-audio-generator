from gtts import gTTS
import os

from .utils import generate_filename, ensure_dir


def text_to_speech(text: str, lang: str = "en", output_dir: str = None) -> str:
    """
    Convert text to speech and save as an MP3 file.
    Single default voice only.
    """
    if output_dir is None:
        output_dir = os.path.join("static", "audio")

    ensure_dir(output_dir)

    filename = generate_filename()
    filepath = os.path.join(output_dir, filename)

    tts = gTTS(text=text, lang=lang)
    tts.save(filepath)

    return filename
