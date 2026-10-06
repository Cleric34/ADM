"""
streamlit_app.py - Main Streamlit Deployment Entrypoint.

Supports direct deployment on Streamlit Community Cloud, Hugging Face Spaces, Render, and local execution.
Provides:
- 📊 Chakravyuha Multi-Agent Simulation & Dashboard
- 🏹 Interactive Turn-Based Strategy Game (2D Grid)
- ⚔️ 3D Kurukshetra Battle Game (3D Three.js)
"""

import os
import sys
import streamlit as st

# Ensure repository root is in Python sys.path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import and execute the full Streamlit dashboard
from app.streamlit_app import *
