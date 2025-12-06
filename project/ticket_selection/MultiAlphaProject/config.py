# config.py - Configuration for Multi-Alpha Strategy
import os
from pathlib import Path

# Get the directory where this config.py file is located
BASE_DIR = Path(__file__).parent

# Paths relative to project structure
INPUT_DIR = str(BASE_DIR.parent / "ticket_selection" / "clusters")
OUTPUT_DIR = str(BASE_DIR / "MultiAlpha_Results")

# --- THAM SỐ ALPHA ---
WINDOW_COINT = 756
WINDOW_Z_SCORE = 60
WINDOW_MOM = 60
WINDOW_VOL_SHORT = 20
WINDOW_VOL_LONG = 60
WINDOW_VALUE = 252

# --- THAM SỐ BACKTEST ---
THRESHOLD_ENTRY = 0.2