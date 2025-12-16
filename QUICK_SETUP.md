# Quick Setup Guide - OpenAI API Key

## Method 1: Interactive Setup (Easiest)

```bash
python setup_api_key.py
```

Follow the prompts to enter your API key.

## Method 2: Environment Variable (Windows PowerShell)

```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
$env:USE_REAL_LLM="true"
python main.py "Your goal"
```

## Method 3: Environment Variable (Windows CMD)

```cmd
set OPENAI_API_KEY=sk-your-api-key-here
set USE_REAL_LLM=true
python main.py "Your goal"
```

## Method 4: .env File (Recommended)

1. Create a file named `.env` in the project root
2. Add these lines:
```
OPENAI_API_KEY=sk-your-api-key-here
USE_REAL_LLM=true
OPENAI_MODEL=gpt-3.5-turbo
```

3. Install python-dotenv:
```bash
pip install python-dotenv
```

4. Run the program - it will automatically load the .env file

## Verify It's Working

Run:
```bash
python main.py "Test goal"
```

If you see:
```
Using OpenAI API: gpt-3.5-turbo
```
Then it's working!

If you see:
```
Using Mock LLM (set OPENAI_API_KEY to use real API)
```
Then check your API key setup.

## Get Your API Key

1. Visit: https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

## Install Required Package

```bash
pip install openai python-dotenv
```

Or install all requirements:
```bash
pip install -r requirements.txt
```


