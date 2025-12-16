# OpenAI API Key Setup Guide

## Quick Setup

### Option 1: Interactive Setup (Recommended)
```bash
python setup_api_key.py
```
Follow the prompts to enter your API key.

### Option 2: Environment Variable
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"
$env:USE_REAL_LLM="true"

# Windows CMD
set OPENAI_API_KEY=your-api-key-here
set USE_REAL_LLM=true

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
export USE_REAL_LLM="true"
```

### Option 3: .env File (Recommended for persistence)

1. Copy the example file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API key:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
USE_REAL_LLM=true
```

3. Install python-dotenv (if not already installed):
```bash
pip install python-dotenv
```

The `.env` file will be automatically loaded when you run `main.py`.

## Get Your API Key

1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (it starts with `sk-`)

## Verify Setup

Run the program:
```bash
python main.py "Test goal"
```

If configured correctly, you'll see:
```
Using OpenAI API: gpt-3.5-turbo
```

If not configured, you'll see:
```
Using Mock LLM (set OPENAI_API_KEY to use real API)
```

## Configuration Options

You can set these environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `USE_REAL_LLM`: Set to "true" to use real API (default: "false")
- `OPENAI_MODEL`: Model to use (default: "gpt-3.5-turbo")
- `LLM_MAX_TOKENS`: Maximum tokens per request (default: 1000)
- `LLM_TEMPERATURE`: Temperature setting (default: 0.7)

## Notes

- The system will automatically fall back to mock LLM if API key is not set
- Mock LLM works for testing but provides basic responses
- Real API provides better quality but requires API credits
- Keep your API key secure and never commit it to version control


