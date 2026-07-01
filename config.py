from pathlib import Path
import json
import os

PROJECT_ROOT = Path(__file__).parent
CONFIG_FILE = PROJECT_ROOT / "config.json"

DEFAULTS = {
    "LLM_BASE_URL": "http://127.0.0.1:11434/v1",
    "LLM_MODEL": "qwen2.5:7b",
    "LLM_API_KEY": "",
    "LLM_TEMPERATURE": 0.7,
    "LLM_MAX_TOKENS": 16384,
    "VOXCPM2_SCRIPT": str(PROJECT_ROOT / "tools" / "VoxCPM2" / "tts.py"),
    "WHISPER_CPP_EXE": str(PROJECT_ROOT / "tools" / "whisper-cli.exe"),
    "WHISPER_MODEL": str(PROJECT_ROOT / "tools" / "ggml-small.bin"),
    "FFMPEG_EXE": str(PROJECT_ROOT / "tools" / "ffmpeg.exe"),
    "OUTPUT_DIR": str(PROJECT_ROOT / "output"),
    "VIDEO_WIDTH": 1920,
    "VIDEO_HEIGHT": 1080,
    "VIDEO_CODEC": "libx264",
    "AUDIO_CODEC": "aac",
    "OUTPUT_FORMAT": "mp4",
}


def _load_user_config():
    cfg = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return cfg


_user = _load_user_config()


def _get(key: str):
    val = _user.get(key)
    if val is not None and val != "":
        return val
    return DEFAULTS.get(key)


LLM_BASE_URL = _get("LLM_BASE_URL")
LLM_MODEL = _get("LLM_MODEL")
LLM_API_KEY = _get("LLM_API_KEY")
LLM_TEMPERATURE = float(_get("LLM_TEMPERATURE") or DEFAULTS["LLM_TEMPERATURE"])
LLM_MAX_TOKENS = int(_get("LLM_MAX_TOKENS") or DEFAULTS["LLM_MAX_TOKENS"])

VOXCPM2_SCRIPT = _get("VOXCPM2_SCRIPT")
WHISPER_CPP_EXE = _get("WHISPER_CPP_EXE")
WHISPER_MODEL = _get("WHISPER_MODEL")
FFMPEG_EXE = _get("FFMPEG_EXE")

OUTPUT_DIR = Path(_get("OUTPUT_DIR") or DEFAULTS["OUTPUT_DIR"])

_tools_dir = str(PROJECT_ROOT / "tools")
if _tools_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _tools_dir + os.pathsep + os.environ.get("PATH", "")

VIDEO_WIDTH = int(_get("VIDEO_WIDTH") or DEFAULTS["VIDEO_WIDTH"])
VIDEO_HEIGHT = int(_get("VIDEO_HEIGHT") or DEFAULTS["VIDEO_HEIGHT"])
VIDEO_CODEC = _get("VIDEO_CODEC")
AUDIO_CODEC = _get("AUDIO_CODEC")
OUTPUT_FORMAT = _get("OUTPUT_FORMAT")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
