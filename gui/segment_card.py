from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QTextEdit, QFileDialog,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QDesktopServices
from pathlib import Path

from config import OUTPUT_DIR


class SegmentCard(QFrame):
    text_changed = Signal(int)
    media_selected = Signal(int, str)

    def __init__(self, seg_data: dict, parent=None):
        super().__init__(parent)
        self.seg_data = seg_data
        self.seg_id = seg_data["id"]
        self._collapsed = False
        self._init_ui()
        self._refresh()

    def _init_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setStyleSheet("SegmentCard { border: 1px solid #ccc; border-radius: 4px; margin: 2px; }")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(8, 6, 8, 6)

        header = QHBoxLayout()
        self.btn_toggle = QPushButton(f"Segment {self.seg_id}")
        self.btn_toggle.setStyleSheet("QPushButton { font-weight: bold; text-align: left; border: none; }")
        self.btn_toggle.clicked.connect(self._toggle)
        header.addWidget(self.btn_toggle)

        self.lbl_status = QLabel("")
        header.addWidget(self.lbl_status)
        header.addStretch()
        self._main_layout.addLayout(header)

        self._body = QWidget()
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(0, 0, 0, 0)

        self.te_text = QTextEdit()
        self.te_text.setMaximumHeight(80)
        self.te_text.setPlaceholderText("段落文案...")
        self.te_text.textChanged.connect(self._on_text_changed)
        body_layout.addWidget(self.te_text)

        info_row = QHBoxLayout()
        self.lbl_dur = QLabel("时长: --")
        info_row.addWidget(self.lbl_dur)
        self.lbl_narration = QLabel("配音: --")
        info_row.addWidget(self.lbl_narration)
        self.lbl_subtitle = QLabel("字幕: --")
        info_row.addWidget(self.lbl_subtitle)
        info_row.addStretch()
        body_layout.addLayout(info_row)

        btn_row = QHBoxLayout()
        self.btn_play_audio = QPushButton("▶ 播放配音")
        self.btn_play_audio.setEnabled(False)
        self.btn_play_audio.clicked.connect(self._play_audio)
        btn_row.addWidget(self.btn_play_audio)

        self.btn_pick_media = QPushButton("选择素材")
        self.btn_pick_media.clicked.connect(self._pick_media)
        btn_row.addWidget(self.btn_pick_media)

        self.lbl_media = QLabel("素材: (未选择)")
        btn_row.addWidget(self.lbl_media)

        self.btn_preview_media = QPushButton("👁 预览")
        self.btn_preview_media.setEnabled(False)
        self.btn_preview_media.clicked.connect(self._preview_media)
        btn_row.addWidget(self.btn_preview_media)

        btn_row.addStretch()
        body_layout.addLayout(btn_row)

        self._main_layout.addWidget(self._body)

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._body.setVisible(not self._collapsed)

    def _refresh(self):
        d = self.seg_data
        self.te_text.blockSignals(True)
        self.te_text.setPlainText(d.get("text", ""))
        self.te_text.blockSignals(False)

        self.lbl_dur.setText(f"时长: {d.get('duration_seconds', 0)}s")

        nar_path = d.get("narration_path", "")
        if nar_path and Path(nar_path).exists():
            self.lbl_narration.setText(f"配音: {Path(nar_path).name}")
            self.btn_play_audio.setEnabled(True)
        else:
            self.lbl_narration.setText("配音: --")
            self.btn_play_audio.setEnabled(False)

        sub_path = d.get("subtitle_path", "")
        if sub_path and Path(sub_path).exists():
            self.lbl_subtitle.setText(f"字幕: {Path(sub_path).name}")
        else:
            self.lbl_subtitle.setText("字幕: --")

        media_path = d.get("media_path", "")
        if media_path and Path(media_path).exists():
            self.lbl_media.setText(f"素材: {Path(media_path).name}")
            self.btn_preview_media.setEnabled(True)
        else:
            self.lbl_media.setText("素材: (未选择)")
            self.btn_preview_media.setEnabled(False)

        if d.get("text_dirty", False):
            self.lbl_status.setText("⬜ 文案已修改")
            self.lbl_status.setStyleSheet("color: #e67e22;")
        else:
            self.lbl_status.setText("")
            self.lbl_status.setStyleSheet("")

    def _on_text_changed(self):
        new_text = self.te_text.toPlainText()
        if new_text != self.seg_data.get("text", ""):
            self.seg_data["text"] = new_text
            self.seg_data["text_dirty"] = True
            self.lbl_status.setText("⬜ 文案已修改")
            self.lbl_status.setStyleSheet("color: #e67e22;")
            self.text_changed.emit(self.seg_id)

    def _pick_media(self):
        path, _ = QFileDialog.getOpenFileName(
            self, f"选择 Segment {self.seg_id} 的素材",
            "",
            "媒体文件 (*.mp4 *.mov *.avi *.png *.jpg *.jpeg);;所有文件 (*.*)"
        )
        if path:
            ext = Path(path).suffix.lower()
            self.seg_data["media_path"] = path
            self.seg_data["media_type"] = "video" if ext in (".mp4", ".mov", ".avi") else "image"
            self._refresh()
            self.media_selected.emit(self.seg_id, path)

    def _play_audio(self):
        nar = self.seg_data.get("narration_path", "")
        if nar and Path(nar).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(nar))

    def _preview_media(self):
        media = self.seg_data.get("media_path", "")
        if media and Path(media).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(media))

    def update_data(self, seg_data: dict):
        self.seg_data = seg_data
        self._refresh()
