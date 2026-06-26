import subprocess
import os
import sys
import wave
from pathlib import Path
from config import VOXCPM2_SCRIPT, OUTPUT_DIR, FFMPEG_EXE


class TTSEngine:
    def __init__(self):
        self.voxcpm2 = Path(VOXCPM2_SCRIPT) if VOXCPM2_SCRIPT else None

    def generate_single(self, text: str, output_path: str):
        if self.voxcpm2 and self.voxcpm2.exists():
            self._generate_voxcpm2(text, output_path)
        else:
            self._generate_fallback(text, output_path)

    def _generate_voxcpm2(self, text: str, output_path: str):
        cmd = [
            sys.executable, str(self.voxcpm2),
            "--text", text,
            "--output", str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(f"VoxCPM2 配音失败: {result.stderr}")

    def _generate_fallback(self, text: str, output_path: str):
        sample_rate = 24000
        duration = len(text) / 3.5
        num_samples = int(sample_rate * max(duration, 1))
        num_channels = 1
        sample_width = 2

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(out), "w") as wf:
            wf.setnchannels(num_channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sample_rate)
            wf.writeframes(b"\x00" * (num_samples * sample_width))
