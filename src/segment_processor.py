import json
from pathlib import Path
from src.tts_engine import TTSEngine
from src.subtitle_generator import SubtitleGenerator
from config import OUTPUT_DIR


class SegmentProcessor:
    def __init__(self):
        self.tts = TTSEngine()
        self.subtitle = SubtitleGenerator()

    def process_all(self, data: dict, log_callback=None) -> dict:
        segments = data.get("segments", [])
        for seg in segments:
            self._log(f"[Segment {seg['id']}] 处理中...", log_callback)
            self._process_one(seg, log_callback)
        return data

    def _process_one(self, seg: dict, log_callback=None):
        seg_id = seg["id"]
        text = seg.get("text", "")
        duration = float(seg.get("duration_seconds", 5))

        if not text.strip():
            self._log(f"[Segment {seg_id}] 跳过（空文本）", log_callback)
            return

        narration_path = OUTPUT_DIR / f"narration_{seg_id:03d}.wav"
        self._log(f"[Segment {seg_id}] 生成配音...", log_callback)
        self.tts.generate_single(text, str(narration_path))
        seg["narration_path"] = str(narration_path)
        seg["text_dirty"] = False

        if narration_path.exists():
            self._log(f"[Segment {seg_id}] 生成字幕...", log_callback)
            subtitle_path = self.subtitle.generate(str(narration_path))
            seg["subtitle_path"] = str(subtitle_path) if subtitle_path else ""
        else:
            seg["subtitle_path"] = ""

        self._log(f"[Segment {seg_id}] 完成", log_callback)

    def _log(self, msg: str, log_callback=None):
        if log_callback:
            log_callback(msg)
