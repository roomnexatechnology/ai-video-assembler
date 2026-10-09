# ai-video-assembler 🎬

**Free** video assembly with GitHub Actions — AI clips + subtitles + audio → final mobile-ready MP4. Zero cost (public repo = unlimited free Actions minutes).

## How it works

1. Generate clips with any free AI video tool (see `hf-video` skill: Pollinations still → LTX image-to-video)
2. Put them in `input/jobs/<job_id>/`:
   ```
   input/jobs/job1/
     clips/s0.mp4 … s7.mp4   # 8 vertical clips (≥ segment length each)
     subs.ass                # libass subtitles timed to narration
     audio.m4a               # final mixed audio (narration + music)
     manifest.json           # optional: {"boundaries": [...], "total": 30.0}
   ```
3. Push, then **Actions → Assemble video (free) → Run workflow** (enter job_id)
4. Download `final-<job_id>` artifact → `dist/final.mp4`

## Output

1080×1920, 30fps, H.264 Baseline + AAC + faststart — plays on any phone.

## Notes

- Default segment boundaries match the KK agency ad v5 narration (8 segments + end card).
- Override with `manifest.json` for other scripts.
- `scripts/assemble.py` also runs locally: `python3 scripts/assemble.py job1`.
