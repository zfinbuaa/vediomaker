import argparse
import sys

if sys.version_info < (3, 10):
    sys.exit(
        f"VideoMaker 需要 Python 3.10+，当前: Python {sys.version}\n"
        "请使用更高版本 Python 运行，例如:\n"
        "  python main.py              (确保 PATH 中 Python >= 3.10)\n"
        "  python main.py --cli --doc README.md\n"
    )


def main():
    parser = argparse.ArgumentParser(description="VideoMaker - 视频文案编辑器")
    parser.add_argument("--doc", default="README.md", help="输入的 .md 文档路径")
    parser.add_argument("--cli", action="store_true", help="命令行模式（无 GUI）")
    args = parser.parse_args()

    if args.cli:
        from src.segment_generator import SegmentGenerator
        from src.segment_processor import SegmentProcessor
        from src.video_compositor import VideoCompositor

        print("=" * 40)
        print("  VideoMaker CLI")
        print("=" * 40)

        gen = SegmentGenerator()
        data = gen.generate(args.doc)
        gen.save(data)
        print(f"文案已生成: {len(data.get('segments', []))} 段")

        proc = SegmentProcessor()
        data = proc.process_all(data)
        print("配音+字幕已完成")

        comp = VideoCompositor()
        output = comp.compose(data)
        print(f"合成完毕: {output}")
    else:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QPushButton { padding: 6px 14px; border: 1px solid #999; border-radius: 3px; background: #e0e0e0; }
            QPushButton:hover { background: #d0d0d0; }
            QPushButton:pressed { background: #c0c0c0; }
            QPushButton:disabled { background: #f0f0f0; color: #999; }
            QLineEdit { padding: 4px; border: 1px solid #aaa; border-radius: 2px; }
            QTextEdit { border: 1px solid #aaa; border-radius: 2px; }
            QGroupBox { font-weight: bold; }
        """)

        window = MainWindow()
        window.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
