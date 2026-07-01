import subprocess
import sys
import wave
from pathlib import Path
from config import VOXCPM2_SCRIPT, FFMPEG_EXE


class TTSEngine:
    VOXCPM2 = "voxcpm2"
    SAPI = "sapi"
    FALLBACK = "silent"

    def __init__(self):
        self.voxcpm2 = Path(VOXCPM2_SCRIPT) if VOXCPM2_SCRIPT else None
        self._active_backend = None
        self._sapi_voice = None

    def _detect_backend(self) -> str:
        if self.voxcpm2 and self.voxcpm2.exists():
            self._active_backend = self.VOXCPM2
            return self._active_backend

        try:
            from win32com.client import Dispatch
            v = Dispatch("SAPI.SpVoice")
            voices = v.GetVoices()
            for i in range(voices.Count):
                name = voices.Item(i).GetDescription()
                if "Chinese" in name or "Huihui" in name or "Hanhan" in name:
                    self._sapi_voice = voices.Item(i)
                    break
            if not self._sapi_voice and voices.Count > 0:
                self._sapi_voice = voices.Item(0)
            if self._sapi_voice:
                self._active_backend = self.SAPI
                return self._active_backend
        except Exception as e:
            print(f"[TTS] SAPI 不可用: {e}")

        self._active_backend = self.FALLBACK
        return self._active_backend

    def generate_single(self, text: str, output_path: str):
        self._active_backend = self._detect_backend()

        if self._active_backend == self.VOXCPM2:
            self._generate_voxcpm2(text, output_path)
        elif self._active_backend == self.SAPI:
            self._generate_sapi(text, output_path)
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

    def _generate_sapi(self, text: str, output_path: str):
        from win32com.client import Dispatch

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        voice = Dispatch("SAPI.SpVoice")
        if self._sapi_voice:
            voice.Voice = self._sapi_voice
        voice.Rate = 0

        tmp_wav = out.with_suffix(".tmp.wav")
        stream = Dispatch("SAPI.SpFileStream")
        stream.Open(str(tmp_wav), 3, False)
        voice.AudioOutputStream = stream
        voice.Speak(text)
        stream.Close()

        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(tmp_wav),
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(out),
        ]
        subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
        tmp_wav.unlink(missing_ok=True)

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
