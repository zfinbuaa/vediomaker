import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog,
    QProgressBar, QStatusBar, QSplitter, QGroupBox, QMessageBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor
from pathlib import Path
import json

from config import LLM_BASE_URL, LLM_MODEL, LLM_API_KEY, OUTPUT_DIR, CONFIG_FILE
from gui.segment_list import SegmentList
from gui.worker import SegmentWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VideoMaker - 视频文案编辑器")
        self.resize(900, 780)
        self._worker = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 8, 10, 8)

        root.addLayout(self._build_config_bar())
        root.addLayout(self._build_input_bar())
        root.addLayout(self._build_toolbar())

        self.segment_list = SegmentList()
        root.addWidget(self.segment_list, stretch=1)

        self.lbl_log_title = QLabel("日志输出:")
        root.addWidget(self.lbl_log_title)

        self.te_log = QTextEdit()
        self.te_log.setReadOnly(True)
        self.te_log.setMaximumHeight(120)
        self.te_log.setFont(QFont("Consolas", 9))
        self.te_log.setStyleSheet("QTextEdit { background-color: #1e1e1e; color: #d4d4d4; }")
        root.addWidget(self.te_log)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("就绪 — 请先配置 LLM，然后选择 .md 文档")

    def _build_config_bar(self):
        layout = QHBoxLayout()
        layout.addWidget(QLabel("LLM URL:"))
        self.le_url = QLineEdit(LLM_BASE_URL)
        self.le_url.setMaximumWidth(240)
        layout.addWidget(self.le_url)

        layout.addWidget(QLabel("模型:"))
        self.le_model = QLineEdit(LLM_MODEL)
        self.le_model.setMaximumWidth(150)
        layout.addWidget(self.le_model)

        layout.addWidget(QLabel("API Key:"))
        self.le_api_key = QLineEdit(LLM_API_KEY)
        self.le_api_key.setEchoMode(QLineEdit.Password)
        self.le_api_key.setMaximumWidth(160)
        layout.addWidget(self.le_api_key)

        self.btn_save_cfg = QPushButton("保存配置")
        self.btn_save_cfg.setMaximumWidth(80)
        self.btn_save_cfg.clicked.connect(self._save_config)
        layout.addWidget(self.btn_save_cfg)

        layout.addStretch()
        self._load_config_fields()
        return layout

    def _build_input_bar(self):
        layout = QHBoxLayout()
        layout.addWidget(QLabel("输入文档:"))
        self.le_doc = QLineEdit("README.md")
        layout.addWidget(self.le_doc)

        self.btn_pick_doc = QPushButton("浏览")
        self.btn_pick_doc.setMaximumWidth(50)
        self.btn_pick_doc.clicked.connect(self._pick_doc)
        layout.addWidget(self.btn_pick_doc)
        layout.addStretch()
        return layout

    def _build_toolbar(self):
        layout = QHBoxLayout()
        self.btn_gen_script = QPushButton("📝 生成文案")
        self.btn_gen_script.setMinimumHeight(36)
        self.btn_gen_script.clicked.connect(self._on_gen_script)
        layout.addWidget(self.btn_gen_script)

        self.btn_gen_audio = QPushButton("🎙 全部配音+字幕")
        self.btn_gen_audio.setMinimumHeight(36)
        self.btn_gen_audio.clicked.connect(self._on_gen_audio)
        layout.addWidget(self.btn_gen_audio)

        self.btn_compose = QPushButton("📦 一键合成")
        self.btn_compose.setMinimumHeight(36)
        self.btn_compose.clicked.connect(self._on_compose)
        layout.addWidget(self.btn_compose)

        layout.addStretch()
        return layout

    def _load_config_fields(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.le_url.setText(cfg.get("LLM_BASE_URL", ""))
                self.le_model.setText(cfg.get("LLM_MODEL", ""))
                self.le_api_key.setText(cfg.get("LLM_API_KEY", ""))
            except Exception:
                pass

    def _save_config(self):
        cfg = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            except Exception:
                pass
        cfg["LLM_BASE_URL"] = self.le_url.text().strip()
        cfg["LLM_MODEL"] = self.le_model.text().strip()
        cfg["LLM_API_KEY"] = self.le_api_key.text().strip()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "配置", "配置已保存")

    def _pick_doc(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 Markdown 文档", "", "Markdown (*.md);;所有文件 (*.*)")
        if path:
            self.le_doc.setText(path)

    def _on_gen_script(self):
        doc_path = self.le_doc.text().strip()
        if not doc_path or not Path(doc_path).exists():
            QMessageBox.warning(self, "错误", "请选择有效的 .md 文档")
            return

        self._save_config()
        self._set_buttons_enabled(False)
        self.te_log.clear()
        self._log("开始生成文案...")

        self._worker = SegmentWorker("generate", doc_path=doc_path)
        self._worker.log_signal.connect(self._on_log)
        self._worker.finished_signal.connect(self._on_script_ready)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _on_gen_audio(self):
        data = self.segment_list.get_data()
        if not data.get("segments"):
            QMessageBox.warning(self, "错误", "请先生成文案")
            return

        self._save_config()
        self._set_buttons_enabled(False)
        self._log("开始生成配音+字幕...")

        self._worker = SegmentWorker("process_audio", segments_data=data)
        self._worker.log_signal.connect(self._on_log)
        self._worker.finished_signal.connect(self._on_audio_ready)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _on_compose(self):
        data = self.segment_list.get_data()
        if not data.get("segments"):
            QMessageBox.warning(self, "错误", "没有段落可合成")
            return

        self._save_config()
        self._set_buttons_enabled(False)
        self._log("开始合成视频...")

        self._worker = SegmentWorker("compose", segments_data=data)
        self._worker.log_signal.connect(self._on_log)
        self._worker.finished_signal.connect(self._on_compose_done)
        self._worker.error_signal.connect(self._on_error)
        self._worker.start()

    def _set_buttons_enabled(self, enabled: bool):
        self.btn_gen_script.setEnabled(enabled)
        self.btn_gen_audio.setEnabled(enabled)
        self.btn_compose.setEnabled(enabled)
        self.statusBar.showMessage("运行中..." if not enabled else "就绪")

    def _on_log(self, msg):
        self.te_log.append(msg)
        self.te_log.moveCursor(QTextCursor.End)

    def _on_script_ready(self, data):
        self._set_buttons_enabled(True)
        self._log(f"文案已生成: {len(data.get('segments', []))} 段")
        self.segment_list.load_data(data)
        self._save_segments_to_file(data)

    def _on_audio_ready(self, data):
        self._set_buttons_enabled(True)
        self._log("配音+字幕全部完成")
        self._save_segments_to_file(data)
        for seg in data.get("segments", []):
            self.segment_list.update_card_by_id(seg["id"], seg)

    def _on_compose_done(self, output_path):
        self._set_buttons_enabled(True)
        self._log(f"合成完毕: {output_path}")
        QMessageBox.information(self, "完成", f"视频已生成:\n{output_path}")

    def _on_error(self, msg):
        self._set_buttons_enabled(True)
        self._log(f"错误: {msg}")
        QMessageBox.critical(self, "错误", msg)

    def _save_segments_to_file(self, data):
        path = OUTPUT_DIR / "segments.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _log(self, msg):
        self.te_log.append(msg)
        self.te_log.moveCursor(QTextCursor.End)
