#!/usr/bin/env python3
"""Quick script to set up API key in .env file (SAFE: reads from user input or env)"""

import os
from getpass import getpass

api_key = os.getenv("OPENAI_API_KEY") or getpass("Enter OPENAI_API_KEY (input hidden): ").strip()

if not api_key:
    raise SystemExit("No API key provided. Set OPENAI_API_KEY env var or enter it when prompted.")

env_content = f"""# OpenAI API Configuration
OPENAI_API_KEY={api_key}
USE_REAL_LLM=true
OPENAI_MODEL=gpt-3.5-turbo
LLM_MAX_TOKENS=1000
LLM_TEMPERATURE=0.7
"""

with open(".env", "w", encoding="utf-8") as f:
    f.write(env_content)

print("API key saved to .env file")
print("Note: .env is in .gitignore and will not be committed to git")
