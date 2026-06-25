import subprocess
from pathlib import Path
from config import WHISPER_CPP_EXE, WHISPER_MODEL, OUTPUT_DIR


class SubtitleGenerator:
    def __init__(self):
        self.whisper_exe = WHISPER_CPP_EXE
        self.model = WHISPER_MODEL
        self._cpp_available = None
        self._py_available = None

    def _check_cpp(self) -> bool:
        if self._cpp_available is not None:
            return self._cpp_available
        try:
            result = subprocess.run([self.whisper_exe, "--help"],
                                    capture_output=True, text=True, timeout=10)
            self._cpp_available = (result.returncode == 0)
        except Exception:
            self._cpp_available = False
        return self._cpp_available

    def _check_py(self) -> bool:
        if self._py_available is not None:
            return self._py_available
        try:
            import whisper
            self._py_available = True
        except ImportError:
            self._py_available = False
        return self._py_available

    def generate(self, audio_path: str) -> Path:
        audio = Path(audio_path)
        if not audio.exists():
            return None

        if self._check_cpp():
            return self._generate_cpp(audio)

        if self._check_py():
            return self._generate_python(audio)

        print("[whisper] whisper-cli 和 openai-whisper 均不可用，跳过字幕生成")
        print("[whisper] 安装方式1: 下载 whisper-cli.exe 到 tools/")
        print("[whisper] 安装方式2: pip install openai-whisper")
        return None

    def _generate_cpp(self, audio: Path) -> Path:
        out_base = audio.with_suffix("")
        cmd = [
            self.whisper_exe,
            "-m", str(self.model) if Path(self.model).exists() or "/" in str(self.model) else self.model,
            "-f", str(audio),
            "-osrt",
            "-of", str(out_base),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                print(f"[whisper] cpp 转录失败: {result.stderr[:300]}")
                return None
        except FileNotFoundError:
            print(f"[whisper] {self.whisper_exe} 未找到")
            return None
        except subprocess.TimeoutExpired:
            print("[whisper] cpp 转录超时")
            return None

        srt_path = Path(str(out_base) + ".srt")
        if srt_path.exists():
            print(f"[whisper] 字幕: {srt_path}")
            return srt_path
        return None

    def _generate_python(self, audio: Path) -> Path:
        import whisper
        import warnings

        warnings.filterwarnings("ignore")
        print("[whisper] 使用 Python openai-whisper 引擎...")
        srt_path = audio.with_suffix(".srt")

        try:
            model_size = "small"
            print(f"[whisper] 加载模型 {model_size}...")
            model = whisper.load_model(model_size)
            print("[whisper] 转录中...")
            result = model.transcribe(str(audio), language="zh", verbose=False)

            with open(srt_path, "w", encoding="utf-8") as f:
                for i, seg in enumerate(result.get("segments", []), 1):
                    start = seg["start"]
                    end = seg["end"]
                    text = seg["text"].strip()
                    f.write(f"{i}\n")
                    f.write(f"{self._fmt_time(start)} --> {self._fmt_time(end)}\n")
                    f.write(f"{text}\n\n")

            print(f"[whisper] 字幕: {srt_path}")
            return srt_path
        except Exception as e:
            print(f"[whisper] Python 转录失败: {e}")
            return None

    def _fmt_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
