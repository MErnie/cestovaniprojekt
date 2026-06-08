"""Krok 4: programovy strih a render pres FFmpeg.

Vertikalni video 1080x1920. Pro kazdou scenu: pozadi + velky overlay text +
vypalene titulky (z SRT) + audio. Sceny se spoji do finalniho .mp4.
"""
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


def _font() -> str | None:
    for p in _FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def _duration(path: str) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path]
    )
    return float(out.strip())


def _prepare_background(scene_idx: int, image_url: str, work: str) -> str:
    """Vrati cestu k 1080x1920 pozadi. Z obrazku nabidky, jinak barva z palety."""
    bg = os.path.join(work, f"bg_{scene_idx}.png")
    if image_url:
        try:
            img = os.path.join(work, f"src_{scene_idx}.jpg")
            r = requests.get(image_url, timeout=30)
            r.raise_for_status()
            with open(img, "wb") as f:
                f.write(r.content)
            subprocess.run(
                ["ffmpeg", "-y", "-i", img, "-vf",
                 f"scale={config.WIDTH}:{config.HEIGHT}:force_original_aspect_ratio=increase,"
                 f"crop={config.WIDTH}:{config.HEIGHT},boxblur=0:0,"
                 f"eq=brightness=-0.15", "-frames:v", "1", bg],
                check=True, capture_output=True,
            )
            return bg
        except Exception:
            pass
    color = _PALETTE[scene_idx % len(_PALETTE)]
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i",
         f"color=c={color}:s={config.WIDTH}x{config.HEIGHT}:d=1",
         "-frames:v", "1", bg],
        check=True, capture_output=True,
    )
    return bg


def _render_scene(idx, audio, subs, overlay_text, image_url, work) -> str:
    dur = _duration(audio)
    bg = _prepare_background(idx, image_url, work)

    # overlay text pres soubor -> zadne problemy s escapovanim (%, :, ')
    overlay_file = os.path.join(work, f"overlay_{idx}.txt")
    with open(overlay_file, "w", encoding="utf-8") as f:
        f.write(overlay_text)

    font = _font()
    fontopt = f"fontfile='{font}':" if font else ""
    vf = (
        f"drawtext={fontopt}textfile='{overlay_file}':expansion=none:"
        f"fontcolor=yellow:fontsize=92:borderw=6:bordercolor=black:"
        f"x=(w-text_w)/2:y=h*0.30:line_spacing=12,"
        f"ass='{subs}'"
    )
    out = os.path.join(work, f"scene_{idx}.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-loop", "1", "-i", bg, "-i", audio,
         "-vf", vf, "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-r", str(config.FPS), "-shortest", out],
        check=True, capture_output=True,
    )
    return out


def build_video(script: dict, scene_assets: list, offer: dict, out_path: str) -> str:
    """scene_assets: list dictu {'audio':..., 'srt':...} ve stejnem poradi jako script['scenes']."""
    work = str(config.OUTPUT_DIR / "work")
    os.makedirs(work, exist_ok=True)
    images = offer.get("image_urls", [])

    clips = []
    for i, (scene, assets) in enumerate(zip(script["scenes"], scene_assets)):
        img = images[i % len(images)] if images else ""
        clips.append(_render_scene(i, assets["audio"], assets["subs"],
                                   scene["visual_overlay"], img, work))

    concat_list = os.path.join(work, "concat.txt")
    with open(concat_list, "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
         "-c", "copy", out_path],
        check=True, capture_output=True,
    )
    return out_path
