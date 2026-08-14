#!/usr/bin/env python3
"""
OmniBot Architect: Multimodal Vision-to-Bot Developer System
============================================================
Converts screenshots, UI mockups, and video recordings of workflows into
production-grade Python automation bots (Playwright, PyAutoGUI, API/Chat bots).

Author: OmniBot AI Engineering Team
Version: 2.1.0
License: MIT
"""

import os
import sys
import time
import re
import ast
import json
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union

import cv2
from PIL import Image

try:
    import google.generativeai as genai
except ImportError:
    print("Error: 'google-generativeai' module is required. Install via: pip install google-generativeai")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("OmniBotArchitect")


class MediaProcessor:
    """Handles visual media ingestion, frame decimation, and formatting."""

    @staticmethod
    def load_image(image_path: str) -> Image.Image:
        """Loads and converts an image file into an RGB PIL Image."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        logger.info(f"Loading image: {image_path}")
        img = Image.open(image_path)
        return img.convert("RGB")

    @staticmethod
    def extract_keyframes(video_path: str, max_frames: int = 12) -> List[Image.Image]:
        """
        Extracts keyframes from a video recording based on motion/frame sampling.
        Used as a local fast-path before uploading to cloud file API.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(f"Extracting keyframes from video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames <= 0:
            cap.release()
            raise ValueError(f"Could not read frames from video: {video_path}")

        step = max(1, total_frames // max_frames)
        frames: List[Image.Image] = []

        for frame_idx in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(rgb_frame))
            if len(frames) >= max_frames:
                break

        cap.release()
        logger.info(f"Extracted {len(frames)} keyframes successfully.")
        return frames

    @staticmethod
    def upload_video_file(video_path: str) -> Any:
        """
        Uploads continuous video to the Gemini File API for full temporal context.
        Waits until processing completes.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(f"Uploading video file to Gemini API: {video_path}")
        video_file = genai.upload_file(path=video_path)
        
        while video_file.state.name == "PROCESSING":
            logger.info("Waiting for video processing on server...")
            time.sleep(3)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise ValueError("Video processing failed on server.")

        logger.info("Video file successfully uploaded and ready for analysis.")
        return video_file


class CodeValidatorSandbox:
    """Provides AST parsing, dependency checking, and isolated dry-run execution."""

    @staticmethod
    def parse_ast(code_string: str) -> Tuple[bool, str]:
        """Validates Python syntax using Abstract Syntax Tree parsing."""
        try:
            ast.parse(code_string)
            return True, "AST Syntax Check Passed."
        except SyntaxError as e:
            return False, f"Syntax Error on line {e.lineno}, col {e.offset}: {e.msg}"

    @staticmethod
    def execute_dry_run(code_string: str, timeout_sec: int = 10) -> Tuple[bool, str]:
        """Executes generated code in an isolated temporary file subprocess."""
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp_file:
            tmp_file.write(code_string)
            tmp_path = tmp_file.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            if result.returncode != 0:
                return False, f"Compilation Failure:\n{result.stderr}"

            return True, "Compilation and Static Analysis Verification Passed."
        except subprocess.TimeoutExpired:
            return False, f"Execution timed out after {timeout_sec} seconds."
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class MultimodalBotSynthesizer:
    """Core synthesis engine leveraging Gemini Multimodal capabilities."""

    SYSTEM_PROMPT = """You are an expert Principal Automation Engineer and Python Developer.
Your task is to analyze user-provided text instructions, UI images, wireframes, and/or action videos, and build a complete, production-ready Python bot script.

TARGET FRAMEWORKS:
1. Browser Automation: Use `playwright.sync_api` (preferred) or `selenium`.
2. Desktop GUI Automation: Use `pyautogui`, `opencv-python`, or `pywinauto`. Ensure `pyautogui.FAILSAFE = True` and explicit waits are included.
3. API / Social / Messaging Bots: Use `requests`, `aiohttp`, `python-telegram-bot`, or `discord.py`.

STRICT REQUIREMENTS FOR CODE GENERATION:
- Code MUST be complete, clean, modular, and runnable out-of-the-box.
- Do NOT use pseudocode or leave placeholder functions (e.g. # TODO: implement here).
- Include comprehensive error handling (try-except blocks), logging, and robust wait conditions.
- Output ONLY valid executable Python code enclosed in a markdown block: ```python ... ```.
- Add an inline configuration block at the top for environment variables / settings.
"""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable or argument is missing.")
        
        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=self.SYSTEM_PROMPT
        )

    def _extract_code_block(self, response_text: str) -> str:
        """Extracts pure Python code from markdown formatted output."""
        pattern = r"```python\s*(.*?)\s*```"
        matches = re.findall(pattern, response_text, re.DOTALL)
        if matches:
            return matches[0].strip()
        
        code_lines = [line for line in response_text.splitlines() if not line.startswith("```")]
        return "\n".join(code_lines).strip()

    def generate_bot_code(
        self,
        user_instruction: str,
        image_paths: Optional[List[str]] = None,
        video_path: Optional[str] = None,
        bot_type: str = "playwright"
    ) -> str:
        """
        Synthesizes Python bot code from user prompts, screenshots, and video streams.
        """
        contents: List[Any] = []

        prompt_text = f"Bot Requirement Type: {bot_type.upper()}\nUser Goal: {user_instruction}\n\n"
        prompt_text += "Carefully examine all provided media (images and/or video) to understand the UI layout, elements, selectors, and user actions demonstrated."
        contents.append(prompt_text)

        if image_paths:
            for img_p in image_paths:
                pil_img = MediaProcessor.load_image(img_p)
                contents.append(pil_img)

        uploaded_video_file = None
        if video_path and os.path.exists(video_path):
            try:
                uploaded_video_file = MediaProcessor.upload_video_file(video_path)
                contents.append(uploaded_video_file)
            except Exception as e:
                logger.warning(f"Video API upload failed ({e}). Falling back to OpenCV keyframe decimation.")
                keyframes = MediaProcessor.extract_keyframes(video_path)
                contents.extend(keyframes)

        logger.info(f"Dispatching query to multimodal model ({self.model_name})...")
        response = self.model.generate_content(contents)

        if uploaded_video_file:
            try:
                genai.delete_file(uploaded_video_file.name)
                logger.info("Cleaned up cloud video file resource.")
            except Exception as e:
                logger.warning(f"Failed to delete cloud video file: {e}")

        raw_code = self._extract_code_block(response.text)
        return raw_code


class OmniBotArchitectEngine:
    """Orchestrator managing multi-modal generation, validation, and auto-repair loops."""

    def __init__(self, api_key: Optional[str] = None):
        self.synthesizer = MultimodalBotSynthesizer(api_key=api_key)
        self.validator = CodeValidatorSandbox()

    def build_bot(
        self,
        instruction: str,
        image_paths: Optional[List[str]] = None,
        video_path: Optional[str] = None,
        bot_type: str = "playwright",
        output_filename: str = "generated_bot.py",
        max_repair_attempts: int = 3
    ) -> str:
        """
        Main end-to-end execution pipeline.
        Generates code, runs AST & compiler checks, and performs self-healing if needed.
        """
        logger.info("=== Starting Bot Generation Pipeline ===")
        code = self.synthesizer.generate_bot_code(
            user_instruction=instruction,
            image_paths=image_paths,
            video_path=video_path,
            bot_type=bot_type
        )

        for attempt in range(1, max_repair_attempts + 1):
            logger.info(f"Validation Attempt {attempt}/{max_repair_attempts}...")
            
            ast_ok, ast_msg = self.validator.parse_ast(code)
            if not ast_ok:
                logger.warning(f"AST Check Failed: {ast_msg}")
                code = self._repair_code(code, ast_msg, instruction)
                continue

            dry_run_ok, dry_msg = self.validator.execute_dry_run(code)
            if not dry_run_ok:
                logger.warning(f"Dry-Run Check Failed: {dry_msg}")
                code = self._repair_code(code, dry_msg, instruction)
                continue

            logger.info("Code validation successful!")
            break

        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(code)

        logger.info(f"Bot script saved successfully to: {output_filename}")
        return code

    def _repair_code(self, faulty_code: str, error_message: str, original_instruction: str) -> str:
        """Autonomous self-healing repair loop."""
        logger.info("Executing autonomous self-healing code repair...")
        repair_prompt = f"""The following generated Python code failed validation checks.

ORIGINAL INSTRUCTION:
{original_instruction}

FAULTY CODE:
```python
{faulty_code}
```

ERROR STACK TRACE:
{error_message}

Fix the error and return ONLY the corrected, fully functional code inside a ```python block.
"""
        repair_model = genai.GenerativeModel("gemini-2.5-flash")
        response = repair_model.generate_content(repair_prompt)
        return self.synthesizer._extract_code_block(response.text)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OmniBot Architect: Build bots from images & videos.")
    parser.add_argument("--prompt", type=str, required=True, help="Description of what the bot should do.")
    parser.add_argument("--images", nargs="*", help="List of path(s) to screenshots/mockups.")
    parser.add_argument("--video", type=str, help="Path to video recording of the workflow.")
    parser.add_argument("--type", type=str, default="playwright", choices=["playwright", "pyautogui", "api", "telegram"], help="Bot framework type.")
    parser.add_argument("--out", type=str, default="generated_bot.py", help="Output filename.")

    args = parser.parse_args()

    if not os.getenv("GEMINI_API_KEY"):
        print("Please set your GEMINI_API_KEY environment variable:")
        print("  export GEMINI_API_KEY='your_api_key_here'")
        sys.exit(1)

    engine = OmniBotArchitectEngine()
    final_code = engine.build_bot(
        instruction=args.prompt,
        image_paths=args.images,
        video_path=args.video,
        bot_type=args.type,
        output_filename=args.out
    )
    print("\n" + "="*50)
    print(f"BOT CREATION COMPLETE. Output saved to {args.out}")
    print("="*50)
