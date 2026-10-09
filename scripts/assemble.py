#!/usr/bin/env python3
"""Free video assembly: AI clips + ASS subtitles + audio -> final 1080x1920 MP4.

Input layout (pushed to input/jobs/<job_id>/):
    clips/s0.mp4 ... s7.mp4   8 vertical clips (any length >= segment)
    subs.ass                  libass subtitles (timed to narration)
    audio.m4a                 final mixed audio (narration + music)
    manifest.json             {"boundaries": [...], "total": 30.0} (optional)

Output: dist/final.mp4 (H.264 baseline, yuv420p, AAC, faststart — mobile-safe)
"""
import json
import os
import subprocess
import sys

W, H, FPS = 1080, 1920, 30
DEFAULT_B = [0.0, 1.56, 7.15, 12.07, 14.64, 19.20, 21.34, 23.19, 24.99, 26.48]
DEFAULT_TOTAL = 30.0


def ff(*args):
    print("+", " ".join(str(c) for c in args[:5]), "...", flush=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-y", *args], check=True)


def main() -> int:
    job_id = sys.argv[1] if len(sys.argv) > 1 else "job1"
    root = os.path.join("input", "jobs", job_id)
    clips = os.path.join(root, "clips")
    subs = os.path.join(root, "subs.ass")
    audio = os.path.join(root, "audio.m4a")
    manifest_p = os.path.join(root, "manifest.json")

    B, total = DEFAULT_B, DEFAULT_TOTAL
    if os.path.exists(manifest_p):
        m = json.load(open(manifest_p))
        B = m.get("boundaries", B)
        total = m.get("total", total)

    os.makedirs("dist", exist_ok=True)
    work = os.path.join("dist", "work")
    os.makedirs(work, exist_ok=True)

    # 1. segments
    seg_files = []
    for i in range(8):
        src = os.path.join(clips, f"s{i}.mp4")
        if not os.path.exists(src):
            print(f"MISSING {src}"); return 2
        dur = (B[i + 1] - B[i]) + 0.3
        out = os.path.join(work, f"seg_{i}.mp4")
        vf = (f"trim=0:{dur:.2f},setpts=PTS-STARTPTS,scale={W}:{H},"
              f"eq=contrast=1.03:saturation=1.06,format=yuv420p,fps={FPS}")
        ff("-i", src, "-vf", vf, "-an", "-c:v", "libx264",
           "-preset", "medium", "-crf", "18", out)
        seg_files.append(out)

    # 2. black end card
    card_d = total - B[8] + 0.15
    card = os.path.join(work, "card.mp4")
    ff("-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:d={card_d:.2f}:r={FPS}",
       "-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium",
       "-crf", "18", card)

    # 3. xfade chain
    inputs, fc = [], []
    for i, sf in enumerate(seg_files + [card]):
        inputs += ["-i", sf]
        fc.append(f"[{i}:v]format=yuv420p,fps={FPS},setpts=PTS-STARTPTS[s{i}]")
    prev = "s0"
    for i in range(8):
        off = B[i + 1] - 0.15
        nxt = f"x{i+1}"
        fc.append(f"[{prev}][s{i+1}]xfade=transition=fade:duration=0.3:"
                  f"offset={off:.2f}[{nxt}]")
        prev = nxt
    chained = os.path.join(work, "chained.mp4")
    ff(*inputs, "-filter_complex", ";".join(fc), "-map", f"[{prev}]",
       "-c:v", "libx264", "-preset", "medium", "-crf", "18",
       "-pix_fmt", "yuv420p", chained)

    # 4. subtitles
    subbed = os.path.join(work, "subbed.mp4")
    ff("-i", chained, "-vf", f"ass='{os.path.abspath(subs)}'",
       "-c:v", "libx264", "-preset", "medium", "-crf", "18",
       "-pix_fmt", "yuv420p", subbed)

    # 5. mux audio
    final = os.path.join("dist", "final.mp4")
    ff("-i", subbed, "-i", audio, "-map", "0:v", "-map", "1:a",
       "-t", str(total), "-c:v", "libx264", "-profile:v", "baseline",
       "-level", "4.0", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
       "-c:a", "aac", "-b:a", "128k", "-ar", "44100", final)
    print("DONE:", final)
    return 0


if __name__ == "__main__":
    sys.exit(main())
