"""Tests for ffmpeg argument building and narration job-lifecycle logic (pure)."""

from __future__ import annotations

from boosternews.audio import build_ffmpeg_args
from boosternews.jobs import next_status_after_failure


def test_ffmpeg_args_basic_normalize_and_encode():
    args = build_ffmpeg_args("in.wav", "out.mp3")
    assert args[0] == "ffmpeg"
    assert "-i" in args and "in.wav" in args
    fc = args[args.index("-filter_complex") + 1]
    assert "loudnorm" in fc
    assert "libmp3lame" in args
    assert args[-1] == "out.mp3"


def test_ffmpeg_args_with_intro_outro_concats_three_inputs():
    args = build_ffmpeg_args("in.wav", "out.mp3", intro="intro.mp3", outro="outro.mp3")
    assert args.count("-i") == 3
    fc = args[args.index("-filter_complex") + 1]
    assert "concat=n=3" in fc


def test_ffmpeg_args_can_skip_normalization():
    args = build_ffmpeg_args("in.wav", "out.mp3", normalize=False)
    fc = args[args.index("-filter_complex") + 1]
    assert "loudnorm" not in fc


def test_requeue_until_attempts_exhausted():
    assert next_status_after_failure(1, 3) == "queued"
    assert next_status_after_failure(2, 3) == "queued"
    assert next_status_after_failure(3, 3) == "failed"
    assert next_status_after_failure(4, 3) == "failed"
