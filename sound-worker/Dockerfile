# Home GPU sound-worker. Requires the NVIDIA Container Toolkit on the host (RTX 4060 Ti).
# CUDA runtime base; Torch + coqui-tts (XTTS-v2) are installed for synthesis (task group 4).
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Heavy ML wheels for XTTS-v2 synthesis (large image — needs the GPU host). Torch first (CUDA
# build), then coqui-tts (the maintained XTTS-v2 library).
RUN pip3 install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu124
RUN pip3 install --no-cache-dir coqui-tts
# torchaudio (matching CUDA build) — XTTS imports it. Placed last so the torch + coqui-tts layers
# stay cached; install order doesn't affect runtime imports.
RUN pip3 install --no-cache-dir torchaudio --index-url https://download.pytorch.org/whl/cu124
# coqui-tts 0.27.x asks for transformers>=4.57 but is incompatible with the 5.x line (removed
# isin_mps_friendly). Cap to the last 4.x that still has it.
RUN pip3 install --no-cache-dir "transformers>=4.57,<5"

# F5-TTS engine (better zero-shot fidelity/accent; selected via TTS_ENGINE=f5). It may re-resolve
# transformers — fine, since when F5 is active the coqui/XTTS path isn't imported.
RUN pip3 install --no-cache-dir f5-tts huggingface_hub num2words
# transformers' newer ASR pulls torchcodec (built for CUDA 13 → won't load on cu124). Remove it so
# reference auto-transcription falls back to soundfile.
RUN pip3 uninstall -y torchcodec || true

# Ubuntu 22.04 ships an old setuptools that can't read PEP 621 [project] metadata; upgrade it so
# the package installs under its real name (kept after the heavy layers to preserve their cache).
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel

COPY pyproject.toml ./
COPY src ./src
RUN pip3 install --no-cache-dir .

# XTTS-v2 has non-commercial licensing (Coqui CPML) — review before commercial use.
ENV COQUI_TOS_AGREED=1

CMD ["python3", "-m", "sound_worker"]
