import subprocess
import asyncio
import os
import sys
import wave
from pathlib import Path
from config import VOXCPM2_SCRIPT, OUTPUT_DIR, FFMPEG_EXE


class TTSEngine:
    VOXCPM2 = "voxcpm2"
    EDGE_TTS = "edge_tts"
    SAPI = "sapi"
    FALLBACK = "silent"

    def __init__(self):
        self.voxcpm2 = Path(VOXCPM2_SCRIPT) if VOXCPM2_SCRIPT else None
        self._active_backend = None

    def _detect_backend(self) -> str:
        if self._active_backend:
            return self._active_backend

        if self.voxcpm2 and self.voxcpm2.exists():
            self._active_backend = self.VOXCPM2
            return self._active_backend

        try:
            import edge_tts
            self._active_backend = self.EDGE_TTS
            return self._active_backend
        except ImportError:
            pass

        try:
            import pyttsx3
            e = pyttsx3.init()
            voices = e.getProperty("voices")
            zh = [v for v in voices if "chinese" in v.name.lower() or "zh" in v.id.lower()]
            if zh:
                self._sapi_engine = pyttsx3.init()
                self._sapi_engine.setProperty("voice", zh[0].id)
                self._sapi_engine.setProperty("rate", 160)
                self._active_backend = self.SAPI
                return self._active_backend
        except Exception:
            pass

        self._active_backend = self.FALLBACK
        return self._active_backend

    def generate_single(self, text: str, output_path: str):
        backend = self._detect_backend()

        if backend == self.VOXCPM2:
            self._generate_voxcpm2(text, output_path)
        elif backend == self.EDGE_TTS:
            self._generate_edge_tts(text, output_path)
        elif backend == self.SAPI:
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

    def _generate_edge_tts(self, text: str, output_path: str):
        from edge_tts import Communicate

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        mp3_path = out.with_suffix(".mp3")

        async def _gen():
            voice = self._pick_edge_voice(text)
            c = Communicate(text, voice)
            await c.save(str(mp3_path))

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = concurrent.futures.ThreadPoolExecutor().submit(
                    asyncio.run, _gen()
                )
                future.result(timeout=60)
            else:
                asyncio.run(_gen())
        except RuntimeError:
            asyncio.run(_gen())

        self._mp3_to_wav(mp3_path, out)
        mp3_path.unlink(missing_ok=True)

    def _pick_edge_voice(self, text: str) -> str:
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in text)
        if has_chinese:
            return "zh-CN-XiaoxiaoNeural"
        return "en-US-JennyNeural"

    def _mp3_to_wav(self, mp3_path: Path, wav_path: Path):
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(mp3_path),
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            str(wav_path),
        ]
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(f"MP3 转 WAV 失败: {result.stderr}")

    def _generate_sapi(self, text: str, output_path: str):
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        self._sapi_engine.save_to_file(text, str(out))
        self._sapi_engine.runAndWait()

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
