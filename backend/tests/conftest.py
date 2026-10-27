"""
conftest.py — Add backend/ to sys.path so 'app' is importable during tests.
"""
import sys
import os

# Ensure the backend/ directory is on the path so `from app.layer_d.xxx import ...` works
BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))
