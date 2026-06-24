import json
from pathlib import Path
from src.llm_client import LLMClient
from config import OUTPUT_DIR


class SegmentGenerator:
    def __init__(self, llm: LLMClient = None):
        self.llm = llm or LLMClient()

    def generate(self, doc_path: str) -> dict:
        doc = Path(doc_path).read_text(encoding="utf-8")
        if not doc.strip():
            raise ValueError("文档内容为空")

        result = self.llm.generate_segments(doc)
        for seg in result.get("segments", []):
            seg.setdefault("narration_path", "")
            seg.setdefault("subtitle_path", "")
            seg.setdefault("media_path", "")
            seg.setdefault("media_type", "")
            seg.setdefault("text_dirty", False)
        return result

    def save(self, data: dict) -> Path:
        path = OUTPUT_DIR / "segments.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load(self) -> dict:
        path = OUTPUT_DIR / "segments.json"
        if not path.exists():
            return {"title": "", "segments": []}
        return json.loads(path.read_text(encoding="utf-8"))
