#!/usr/bin/env python3
"""
Example Script: How to use OmniBot Architect programmatically.
"""

import os
from omnibot_architect import OmniBotArchitectEngine

def main():
    # Ensure GEMINI_API_KEY is set in your environment
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable is missing.")
        print("Set it using: export GEMINI_API_KEY='your_key'")
        return

    # Initialize Engine
    engine = OmniBotArchitectEngine()

    # Define build parameters
    instruction = "Create a Playwright bot that opens dynamic web tables, extracts financial metrics, and saves them to a CSV file."
    
    # Optional image mockups or video recording
    images = ["sample_screenshot.png"] if os.path.exists("sample_screenshot.png") else None
    video = "sample_recording.mp4" if os.path.exists("sample_recording.mp4") else None

    print("Synthesizing custom bot script...")
    generated_code = engine.build_bot(
        instruction=instruction,
        image_paths=images,
        video_path=video,
        bot_type="playwright",
        output_filename="my_custom_bot.py"
    )

    print("\n--- GENERATED CODE PREVIEW ---")
    print(generated_code[:500] + "\n...")

if __name__ == "__main__":
    main()
