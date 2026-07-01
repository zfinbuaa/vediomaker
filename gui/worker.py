from PySide6.QtCore import QThread, Signal


class SegmentWorker(QThread):
    log_signal = Signal(str)
    finished_signal = Signal(object)
    error_signal = Signal(str)

    def __init__(self, mode: str, doc_path: str = None, segments_data: dict = None, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.doc_path = doc_path
        self.segments_data = segments_data

    def run(self):
        try:
            if self.mode == "generate":
                self._run_generate()
            elif self.mode == "process_audio":
                self._run_process_audio()
            elif self.mode == "compose":
                self._run_compose()
        except Exception as e:
            self.error_signal.emit(str(e))

    def _run_generate(self):
        from src.segment_generator import SegmentGenerator
        gen = SegmentGenerator()
        data = gen.generate(self.doc_path)
        gen.save(data)
        self.log_signal.emit(f"已生成 {len(data.get('segments', []))} 个段落")
        self.finished_signal.emit(data)

    def _run_process_audio(self):
        import json
        from src.segment_processor import SegmentProcessor
        from config import OUTPUT_DIR
        proc = SegmentProcessor()
        data = proc.process_all(self.segments_data, log_callback=lambda m: self.log_signal.emit(m))
        path = OUTPUT_DIR / "segments.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.finished_signal.emit(data)

    def _run_compose(self):
        from src.video_compositor import VideoCompositor
        comp = VideoCompositor()
        output = comp.compose(self.segments_data, log_callback=lambda m: self.log_signal.emit(m))
        self.finished_signal.emit(str(output))
