"""
Configuration file for AI Agent Orchestrator
Set your OpenAI API key and preferences here.
"""

import os

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
USE_REAL_LLM = os.getenv("USE_REAL_LLM", "false").lower() == "true"

# LLM Settings
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# Orchestrator Settings
DEFAULT_AUTOMATION_LEVEL = os.getenv("AUTOMATION_LEVEL", "semi_automated")
DEFAULT_MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/orchestrator.log")
