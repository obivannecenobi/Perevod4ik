"""Application configuration for the translator app.

API keys and important paths are read from environment variables. You can
set them in your system environment or edit this file directly.
"""
import os

# API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # OpenAI API key
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY", "")    # Deepl API key

# Paths
MODEL_PATH = os.getenv("MODEL_PATH", "/path/to/models")  # Path to translation models
DATA_PATH = os.getenv("DATA_PATH", "/path/to/data")      # Path to additional data
