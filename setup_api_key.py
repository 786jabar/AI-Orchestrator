#!/usr/bin/env python3
"""
Setup script for OpenAI API key configuration
"""

import os
import sys

def setup_api_key():
    """Interactive setup for OpenAI API key"""
    print("=" * 60)
    print("OpenAI API Key Setup")
    print("=" * 60)
    print()
    
    current_key = os.getenv("OPENAI_API_KEY", "")
    if current_key:
        print(f"Current API key: {current_key[:10]}...{current_key[-4:]}")
        use_current = input("Use current key? (y/n): ").lower().strip()
        if use_current == 'y':
            print("\nUsing existing API key from environment.")
            return
    
    print("Enter your OpenAI API key:")
    print("(You can get it from: https://platform.openai.com/api-keys)")
    api_key = input("API Key: ").strip()
    
    if not api_key:
        print("No API key provided. System will use mock LLM.")
        return
    
    print("\nChoose setup method:")
    print("1. Set environment variable (current session)")
    print("2. Create .env file (persistent)")
    print("3. Both")
    
    choice = input("Choice (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["USE_REAL_LLM"] = "true"
        print("\nEnvironment variable set for current session.")
    
    if choice in ['2', '3']:
        env_content = f"""# OpenAI API Configuration
OPENAI_API_KEY={api_key}
USE_REAL_LLM=true
OPENAI_MODEL=gpt-3.5-turbo
LLM_MAX_TOKENS=1000
LLM_TEMPERATURE=0.7
"""
        with open(".env", "w") as f:
            f.write(env_content)
        print(".env file created.")
        print("\nNote: Install python-dotenv to auto-load .env file:")
        print("  pip install python-dotenv")
    
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)
    print("\nTo use the API key:")
    print("  - If using environment variable: Restart your terminal/session")
    print("  - If using .env file: Install python-dotenv and it will auto-load")
    print("\nTest with: python main.py 'Your goal here'")

if __name__ == "__main__":
    setup_api_key()


