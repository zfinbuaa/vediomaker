import subprocess
from pathlib import Path
from config import WHISPER_CPP_EXE, WHISPER_MODEL, OUTPUT_DIR


class SubtitleGenerator:
    def __init__(self):
        self.whisper_exe = WHISPER_CPP_EXE
        self.model = WHISPER_MODEL

    def generate(self, audio_path: str) -> Path:
        audio = Path(audio_path)
        if not audio.exists():
            return None

        out_base = audio.with_suffix("")
        cmd = [
            self.whisper_exe,
            "-m", self.model,
            "-f", str(audio),
            "-osrt",
            "-of", str(out_base),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return None

        srt_path = Path(str(out_base) + ".srt")
        return srt_path if srt_path.exists() else None
