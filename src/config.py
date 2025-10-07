import os

GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set.")

GEMINI_MODEL_2_5_FLASH=os.getenv("GEMINI_MODEL_2_5_FLASH")
if not GEMINI_MODEL_2_5_FLASH:
    raise ValueError("GEMINI_MODEL_2_5_FLASH environment variable is not set.")

GEMINI_MODEL_2_5_FLASH_LIVE=os.getenv("GEMINI_MODEL_2_5_FLASH_LIVE")
if not GEMINI_MODEL_2_5_FLASH_LIVE:
    raise ValueError("GEMINI_MODEL_2_5_FLASH_LIVE environment variable is not set.")