from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QSizePolicy,
)
from PyQt5.QtCore import pyqtSignal
from gui.segment_card import SegmentCard


class SegmentList(QWidget):
    data_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {"title": "", "segments": []}
        self._cards = []

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.addStretch()

        self._scroll.setWidget(self._container)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._scroll)

    def load_data(self, data: dict):
        self._data = data
        self._rebuild_cards()

    def get_data(self) -> dict:
        for card in self._cards:
            seg = card.seg_data
            idx = next((i for i, s in enumerate(self._data["segments"]) if s["id"] == seg["id"]), None)
            if idx is not None:
                self._data["segments"][idx] = seg
        return self._data

    def _rebuild_cards(self):
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        for seg in self._data.get("segments", []):
            card = SegmentCard(seg)
            card.text_changed.connect(self._on_text_changed)
            card.media_selected.connect(self._on_media_selected)
            self._layout.insertWidget(self._layout.count() - 1, card)
            self._cards.append(card)

    def _on_text_changed(self, seg_id):
        self.data_changed.emit(self.get_data())

    def _on_media_selected(self, seg_id, path):
        self.data_changed.emit(self.get_data())

    def update_card_by_id(self, seg_id, seg_data):
        for card in self._cards:
            if card.seg_id == seg_id:
                card.update_data(seg_data)
                break
