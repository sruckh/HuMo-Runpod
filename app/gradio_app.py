#!/usr/bin/env python3
"""Gradio interface for HuMo text/audio/video generation."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import gradio as gr
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "generate.yaml"
DEFAULT_OUTPUT_BASE = Path(os.getenv("OUTPUT_DIR", PROJECT_ROOT / "output"))
RUN_INFERENCE = SCRIPTS_DIR / "run_inference.py"


def load_default_config() -> dict:
    if not DEFAULT_CONFIG.exists():
        return {}
    with DEFAULT_CONFIG.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def ensure_output_dir() -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    output_dir = DEFAULT_OUTPUT_BASE / "gradio" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_command(
    prompt: str,
    audio_path: str,
    image_path: Optional[str],
    negative_prompt: str,
    mode: str,
    height: int,
    width: int,
    frames: int,
    steps: int,
    scale_t: float,
    scale_a: float,
    seed: Optional[int],
    variant: str,
    sp_size: int,
    fps: int,
    output_dir: Path,
) -> list:
    command = [
        sys.executable,
        str(RUN_INFERENCE),
        "--prompt",
        prompt,
        "--audio",
        audio_path,
        "--mode",
        mode,
        "--config",
        str(DEFAULT_CONFIG),
        "--output-dir",
        str(output_dir),
        "--height",
        str(height),
        "--width",
        str(width),
        "--frames",
        str(frames),
        "--steps",
        str(steps),
        "--scale-t",
        str(scale_t),
        "--scale-a",
        str(scale_a),
    ]

    if negative_prompt:
        command.extend(["--negative-prompt", negative_prompt])
    if image_path:
        command.extend(["--image", image_path])
    if seed is not None:
        command.extend(["--seed", str(seed)])
    if variant:
        command.extend(["--variant", variant])
    if sp_size:
        command.extend(["--sp-size", str(sp_size)])
    if fps:
        command.extend(["--fps", str(fps)])

    return command


def run_generation(
    prompt: str,
    negative_prompt: str,
    audio_file: str,
    image_file: Optional[str],
    mode: str,
    height: int,
    width: int,
    frames: int,
    steps: int,
    scale_t: float,
    scale_a: float,
    seed: Optional[int],
    variant: str,
    sp_size: int,
    fps: int,
) -> Tuple[Optional[str], str, Optional[str]]:
    if not audio_file:
        return None, "Please provide an audio file.", None

    output_dir = ensure_output_dir()

    command = build_command(
        prompt=prompt,
        audio_path=audio_file,
        image_path=image_file,
        negative_prompt=negative_prompt,
        mode=mode,
        height=height,
        width=width,
        frames=frames,
        steps=steps,
        scale_t=scale_t,
        scale_a=scale_a,
        seed=seed,
        variant=variant,
        sp_size=sp_size,
        fps=fps,
        output_dir=output_dir,
    )

    completed = subprocess.run(command, capture_output=True, text=True)
    logs = completed.stdout + "\n" + completed.stderr

    manifest_path = output_dir / "request_manifest.json"
    manifest_link = str(manifest_path) if manifest_path.exists() else None

    if completed.returncode != 0:
        return None, f"Inference failed with exit code {completed.returncode}.\n\n{logs}", manifest_link

    config = load_default_config()
    video_filename = (
        (config.get("outputs") or {}).get("video_filename")
        or "humo_output.mp4"
    )
    video_path = output_dir / video_filename

    if not video_path.exists():
        return None, f"Inference completed but video not found at {video_path}.\n\n{logs}", manifest_link

    return str(video_path), logs, manifest_link


def build_interface() -> gr.Blocks:
    default_config = load_default_config()
    generation_defaults = default_config.get("generation", {})
    diffusion_defaults = default_config.get("diffusion", {}).get("timesteps", {}).get("sampling", {})

    default_height = generation_defaults.get("height", 720)
    default_width = generation_defaults.get("width", 1280)
    default_frames = generation_defaults.get("frames", 64)
    default_scale_t = generation_defaults.get("scale_t", 7.5)
    default_scale_a = generation_defaults.get("scale_a", 1.0)
    default_fps = generation_defaults.get("fps", 24)
    default_steps = diffusion_defaults.get("steps", 25)
    default_sp_size = default_config.get("dit", {}).get("sp_size", 1)

    with gr.Blocks(title="HuMo RunPod Generator") as demo:
        gr.Markdown(
            """
            # HuMo RunPod Generator
            Provide a text prompt, conditioning audio, and optional reference image to generate motion videos.
            Configure advanced parameters in the sidebar.
            """
        )

        with gr.Row():
            prompt = gr.Textbox(
                label="Text Prompt",
                lines=3,
                placeholder="Describe the motion to generate...",
            )
            negative_prompt = gr.Textbox(
                label="Negative Prompt",
                lines=3,
                placeholder="Optional negative prompt",
            )

        audio = gr.Audio(label="Conditioning Audio", type="filepath")
        image = gr.Image(label="Reference Image (TIA mode)", type="filepath")

        with gr.Row():
            mode = gr.Radio(
                choices=["TA", "TIA"],
                value=generation_defaults.get("mode", "TA"),
                label="Generation Mode",
            )
            variant = gr.Dropdown(
                choices=["1.7B", "17B"],
                value=default_config.get("model", {}).get("variant", "1.7B"),
                label="Model Variant",
            )
            seed = gr.Number(label="Seed", value=None)

        with gr.Accordion("Advanced Parameters", open=False):
            height = gr.Slider(256, 1536, value=default_height, step=16, label="Height")
            width = gr.Slider(256, 1536, value=default_width, step=16, label="Width")
            frames = gr.Slider(16, 128, value=default_frames, step=8, label="Frames")
            steps = gr.Slider(10, 100, value=default_steps, step=1, label="Sampling Steps")
            scale_t = gr.Slider(0.0, 15.0, value=default_scale_t, step=0.1, label="Text Guidance Scale")
            scale_a = gr.Slider(0.0, 10.0, value=default_scale_a, step=0.1, label="Audio Guidance Scale")
            fps = gr.Slider(1, 60, value=default_fps, step=1, label="Frames Per Second")
            sp_size = gr.Slider(1, 8, value=default_sp_size, step=1, label="Sequence Parallel Size")

        submit = gr.Button("Generate Video", variant="primary")

        video_output = gr.Video(label="Generated Video")
        log_output = gr.Textbox(label="Logs", lines=12)
        manifest_file = gr.File(label="Request Manifest", visible=False)

        def on_submit(prompt, negative_prompt, audio_path, image_path, mode_val, height_val, width_val, frames_val,
                      steps_val, scale_t_val, scale_a_val, fps_val, sp_size_val, seed_val, variant_val):
            if mode_val == "TIA" and not image_path:
                return None, "TIA mode requires a reference image.", None
            video, logs, manifest = run_generation(
                prompt=prompt,
                negative_prompt=negative_prompt or "",
                audio_file=audio_path,
                image_file=image_path if mode_val == "TIA" else None,
                mode=mode_val,
                height=int(height_val),
                width=int(width_val),
                frames=int(frames_val),
                steps=int(steps_val),
                scale_t=float(scale_t_val),
                scale_a=float(scale_a_val),
                fps=int(fps_val),
                sp_size=int(sp_size_val),
                seed=int(seed_val) if seed_val is not None else None,
                variant=variant_val or "",
            )
            video_update = video if video else None
            manifest_update = gr.update(value=manifest, visible=bool(manifest))
            return video_update, logs, manifest_update

        submit.click(
            fn=on_submit,
            inputs=[
                prompt,
                negative_prompt,
                audio,
                image,
                mode,
                height,
                width,
                frames,
                steps,
                scale_t,
                scale_a,
                fps,
                sp_size,
                seed,
                variant,
            ],
            outputs=[video_output, log_output, manifest_file],
        )

    return demo


def main() -> None:
    demo = build_interface()
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("GRADIO_PORT", "7860")), share=os.getenv("GRADIO_SHARE", "false").lower() == "true")


if __name__ == "__main__":
    main()
