import subprocess
import json
import tempfile
from pathlib import Path
from config import FFMPEG_EXE, OUTPUT_DIR, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_CODEC, AUDIO_CODEC


class VideoCompositor:
    def __init__(self):
        self.ffmpeg = FFMPEG_EXE
        self._available = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            result = subprocess.run([self.ffmpeg, "-version"], capture_output=True, encoding="utf-8", errors="replace")
            self._available = (result.returncode == 0)
        except FileNotFoundError:
            self._available = False
        return self._available

    def _check_available(self):
        if not self.is_available():
            raise RuntimeError(
                f"FFmpeg 未找到，请安装后将其路径加入系统 PATH，"
                f"或在 config.json 中设置 FFMPEG_EXE 为绝对路径。\n"
                f"当前配置: FFMPEG_EXE = \"{self.ffmpeg}\"\n"
                f"Windows 安装: winget install Gyan.FFmpeg\n"
                f"或手动下载: https://www.gyan.dev/ffmpeg/builds/"
            )

    def compose(self, data: dict, output_name: str = "output.mp4", log_callback=None) -> Path:
        self._check_available()

        segments = data.get("segments", [])
        output = OUTPUT_DIR / output_name

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            normalized_segments = []

            for i, seg in enumerate(segments):
                seg_id = seg["id"]

                nar_path = seg.get("narration_path", "")
                med_path = seg.get("media_path", "")

                narration = Path(nar_path) if nar_path else None
                media = Path(med_path) if med_path else None

                has_narration = narration and narration.is_file()
                has_media = media and media.is_file()

                if not has_narration and not has_media:
                    continue

                media_dur = self._get_duration(media) if has_media else 0
                audio_dur = self._get_audio_duration(narration) if has_narration else 0

                segment_dur = max(media_dur, audio_dur) if (has_media or has_narration) else 5

                norm_video = tmp / f"norm_v_{i:03d}.mp4"
                norm_audio = tmp / f"norm_a_{i:03d}.aac"

                self._normalize_segment(
                    media, narration, segment_dur,
                    media_dur, audio_dur,
                    norm_video, norm_audio,
                    log_callback
                )
                normalized_segments.append((norm_video, norm_audio))
                self._log(f"[合成] Segment {seg_id}: media={media_dur}s audio={audio_dur}s final={segment_dur}s", log_callback)

            if not normalized_segments:
                raise RuntimeError("没有有效的段落可合成")

            self._concat_all(normalized_segments, output, log_callback)

        self._log(f"[合成] 最终输出: {output}", log_callback)
        return output

    def _normalize_segment(self, media_path, narration_path, target_dur,
                           media_dur, audio_dur, out_video, out_audio, log_callback):
        if media_path and media_path.is_file():
            if media_dur < target_dur:
                cmd_v = [
                    self.ffmpeg, "-y",
                    "-i", str(media_path),
                    "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,tpad=stop_mode=clone:stop_duration={target_dur - media_dur}",
                    "-c:v", VIDEO_CODEC,
                    "-pix_fmt", "yuv420p",
                    "-an",
                    "-shortest",
                    str(out_video),
                ]
            else:
                cmd_v = [
                    self.ffmpeg, "-y",
                    "-i", str(media_path),
                    "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
                    "-c:v", VIDEO_CODEC,
                    "-pix_fmt", "yuv420p",
                    "-an",
                    "-t", str(target_dur),
                    str(out_video),
                ]
        else:
            cmd_v = [
                self.ffmpeg, "-y",
                "-f", "lavfi",
                "-i", f"color=c=black:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d={target_dur}:r=30",
                "-c:v", VIDEO_CODEC,
                "-pix_fmt", "yuv420p",
                "-an",
                str(out_video),
            ]

        result_v = subprocess.run(cmd_v, capture_output=True, encoding="utf-8", errors="replace")
        if result_v.returncode != 0:
            raise RuntimeError(f"视频归一化失败:\n{result_v.stderr}")

        if narration_path and narration_path.is_file():
            if audio_dur < target_dur:
                cmd_a = [
                    self.ffmpeg, "-y",
                    "-i", str(narration_path),
                    "-af", f"apad=pad_dur={target_dur - audio_dur}",
                    "-c:a", AUDIO_CODEC,
                    str(out_audio),
                ]
            else:
                cmd_a = [
                    self.ffmpeg, "-y",
                    "-i", str(narration_path),
                    "-c:a", AUDIO_CODEC,
                    "-t", str(target_dur),
                    str(out_audio),
                ]
            result_a = subprocess.run(cmd_a, capture_output=True, encoding="utf-8", errors="replace")
            if result_a.returncode != 0:
                raise RuntimeError(f"音频归一化失败:\n{result_a.stderr}")
        else:
            cmd_a = [
                self.ffmpeg, "-y",
                "-f", "lavfi",
                "-i", f"anullsrc=r=44100:cl=stereo:d={target_dur}",
                "-c:a", AUDIO_CODEC,
                str(out_audio),
            ]
            subprocess.run(cmd_a, capture_output=True)

    def _concat_all(self, segments, output, log_callback):
        ffmpeg_inputs = []
        map_parts_v = []
        map_parts_a = []

        for i, (v, a) in enumerate(segments):
            ffmpeg_inputs += ["-i", str(v)]
            ffmpeg_inputs += ["-i", str(a)]
            map_parts_v.append(f"[{i*2}:v]")
            map_parts_a.append(f"[{i*2+1}:a]")

        concat_v_inputs = "".join(map_parts_v)
        concat_a_inputs = "".join(map_parts_a)
        filter_str = f"{concat_v_inputs}concat=n={len(segments)}:v=1:a=0[vout];{concat_a_inputs}concat=n={len(segments)}:v=0:a=1[aout]"

        cmd = [self.ffmpeg, "-y"] + ffmpeg_inputs + [
            "-filter_complex", filter_str,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", VIDEO_CODEC,
            "-c:a", AUDIO_CODEC,
            "-pix_fmt", "yuv420p",
            str(output),
        ]

        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(f"拼接失败:\n{result.stderr}")

    def _get_duration(self, path: Path) -> float:
        try:
            cmd = [self.ffmpeg, "-i", str(path), "-f", "null", "-"]
            result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
            stderr = result.stderr
            for line in stderr.split("\n"):
                if "Duration" in line:
                    parts = line.strip().split("Duration: ")[1].split(",")[0]
                    h, m, s = parts.split(":")
                    return float(h) * 3600 + float(m) * 60 + float(s)
        except Exception:
            pass
        return 5.0

    def _get_audio_duration(self, path: Path) -> float:
        return self._get_duration(path)

    def _log(self, msg: str, log_callback=None):
        if log_callback:
            log_callback(msg)
