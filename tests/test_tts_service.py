import os
from backend.audio_engine.tts_service import text_to_speech


def test_text_to_speech_creates_file(tmp_path):
    text = "Hello, this is a test."
    output_dir = tmp_path / "audio"
    filename = text_to_speech(text=text, lang="en", output_dir=str(output_dir))

    filepath = output_dir / filename
    assert filepath.exists()
    assert filepath.suffix == ".mp3"
