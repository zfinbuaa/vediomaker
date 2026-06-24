# VideoMaker — 视频文案编辑器

基于本地 LLM 的半自动视频制作工具：LLM 生成分段文案 → 人工录制/选择素材 → 一键合成。

```
.md 文档 ──► LLM ──► segments.json (N段文案)
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Segment 1   Segment 2   Segment 3
         [可编辑文案]  [可编辑文案]  [可编辑文案]
              │          │          │
         [生成配音+字幕]  │          │
              │          │          │
          配音.wav    配音.wav    配音.wav
          字幕.srt    字幕.srt    字幕.srt
              │          │          │
         [用户选择素材: mp4/png/jpg]
              │          │          │
              └──────────┼──────────┘
                         ▼
         ┌──── 每段归一化处理 ────┐
         │ 语音<视频 → 视频播完   │
         │ 视频<语音 → 定格末帧   │
         └───────────────────────┘
                         ▼
              FFmpeg concat 多段拼接
                         │
                         ▼
                    output.mp4
```

## 依赖

- Python 3.8+
- [VoxCPM2](https://github.com/thuhcsi/VoxCPM2) — TTS 配音（可选，无则生成静默占位）
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) — 语音转字幕（可选）
- [FFmpeg](https://ffmpeg.org/) — 视频合成
- 本地 LLM（OpenAI 兼容 API）

## 使用

```bash
pip install -r requirements.txt
python main.py              # 启动 GUI
python main.py --cli --doc README.md   # 命令行模式
```

## GUI 操作流程

1. **配置**：顶部填入 LLM URL、模型名、API Key，点击保存
2. **选择文档**：浏览选择 .md 文件
3. **生成文案**：LLM 将文档拆分为多个段落，显示在下方卡片列表
4. **编辑文案**：可随时修改卡片中的文案文本
5. **配音+字幕**：点击按钮生成所有段落的 .wav 和 .srt
6. **选择素材**：每个段落点击「选择素材」插入视频或图片
7. **一键合成**：FFmpeg 自动处理时长差异并拼接输出
