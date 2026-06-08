"""Krok 4: render pres FFmpeg.

Vertikalni 1080x1920. Kazda scena: fotka s Ken Burns pohybem (pomaly zoom/pan) +
velky overlay text + vypalene karaoke titulky + audio. Sceny se spoji a pod cele
video se primixuje hudba z assets/music/ (kdyz tam nejaka je).
"""
import glob
import os
import subprocess
import requests
import config

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
_PALETTE = ["0x12343b", "0x1d3557", "0x2a1a3a", "0x0f2027", "0x3a1c1c"]
_BIG_W, _BIG_H = 2160, 3840  # vysoke rozliseni pro plynuly Ken Burns


def _font():
    for p in _FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def _duration(path: str) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path])
    return float(out.strip())


def _prepare_background(idx: int, image_url: str, work: str) -> str:
    bg = os.path.join(work, f"bg_{idx}.png")
    if image_url:
        try:
            img = os.path.join(work, f"src_{idx}.jpg")
            if os.path.exists(image_url):           # lokalni soubor
                img = image_url
            else:                                    # URL
                r = requests.get(image_url, timeout=30)
                r.raise_for_status()
                with open(img, "wb") as f:
                    f.write(r.content)
            subprocess.run(
                ["ffmpeg", "-y", "-i", img, "-vf",
                 f"scale={_BIG_W}:{_BIG_H}:force_original_aspect_ratio=increase,"
                 f"crop={_BIG_W}:{_BIG_H},eq=brightness=-0.12", "-frames:v", "1", bg],
                check=True, capture_output=True)
            return bg
        except Exception:
            pass
    color = _PALETTE[idx % len(_PALETTE)]
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s={_BIG_W}x{_BIG_H}:d=1",
         "-frames:v", "1", bg], check=True, capture_output=True)
    return bg


def _ken_burns(idx: int, frames: int) -> str:
    """Stridani zoom-in / pan pro vizualni rozmanitost. Vystup 1080x1920@fps."""
    s = f"s={config.WIDTH}x{config.HEIGHT}:fps={config.FPS}:d={frames}"
    if idx % 2 == 0:
        return (f"zoompan=z='min(zoom+0.0010,1.15)':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':{s}")
    return (f"zoompan=z=1.12:x='(iw-iw/zoom)*on/{max(frames,1)}':"
            f"y='ih/2-(ih/zoom/2)':{s}")


def _render_scene(idx, audio, subs, overlay_text, image_url, work) -> str:
    dur = _duration(audio)
    frames = max(int(dur * config.FPS) + 2, 2)
    bg = _prepare_background(idx, image_url, work)

    overlay_file = os.path.join(work, f"overlay_{idx}.txt")
    with open(overlay_file, "w", encoding="utf-8") as f:
        f.write(overlay_text)

    font = _font()
    fontopt = f"fontfile='{font}':" if font else ""
    vf = (
        f"{_ken_burns(idx, frames)},"
        f"drawtext={fontopt}textfile='{overlay_file}':expansion=none:"
        f"fontcolor=yellow:fontsize=92:borderw=6:bordercolor=black:"
        f"x=(w-text_w)/2:y=h*0.30:line_spacing=12,"
        f"ass='{subs}'"
    )
    out = os.path.join(work, f"scene_{idx}.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-i", bg, "-i", audio,
         "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]", "-map", "1:a",
         "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-r", str(config.FPS), "-shortest", out],
        check=True, capture_output=True)
    return out


def _find_music():
    for ext in ("mp3", "m4a", "wav", "aac"):
        hits = glob.glob(str(config.ASSETS_DIR / "music" / f"*.{ext}"))
        if hits:
            return hits[0]
    return None


def _add_music(video_in: str, out_path: str):
    music = _find_music()
    if not music:
        os.replace(video_in, out_path)
        return
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_in, "-stream_loop", "-1", "-i", music,
         "-filter_complex",
         f"[1:a]volume={config.MUSIC_VOLUME}[m];"
         f"[0:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac",
         "-shortest", out_path],
        check=True, capture_output=True)


def build_video(script: dict, scene_assets: list, image_urls: list, out_path: str) -> str:
    work = str(config.OUTPUT_DIR / "work")
    os.makedirs(work, exist_ok=True)
    pool = image_urls or []

    clips = []
    for i, (scene, assets) in enumerate(zip(script["scenes"], scene_assets)):
        img = pool[i % len(pool)] if pool else ""
        clips.append(_render_scene(i, assets["audio"], assets["subs"],
                                   scene["visual_overlay"], img, work))

    concat_list = os.path.join(work, "concat.txt")
    with open(concat_list, "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    joined = os.path.join(work, "joined.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
         "-c", "copy", joined], check=True, capture_output=True)

    _add_music(joined, out_path)
    return out_path
