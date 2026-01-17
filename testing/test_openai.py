#!/usr/bin/env python3
"""Test OpenAI API connection and model availability."""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Test 1: List available GPT models
print("=== Available GPT Models ===")
models = client.models.list()
gpt_models = [m.id for m in models.data if "gpt" in m.id.lower()]
for m in sorted(gpt_models):
    print(f"  {m}")

# Test 2: Test chat completion
print("\n=== Testing Chat Completion ===")
test_models = ["gpt-5.2-pro", "gpt-5.2", "gpt-4o"]

for model in test_models:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Say 'test ok' in 2 words"}],
            max_tokens=10
        )
        print(f"  ✓ {model}: {response.choices[0].message.content}")
    except Exception as e:
        print(f"  ✗ {model}: {str(e)[:60]}")

# Test 3: Test structured outputs (beta)
print("\n=== Testing Structured Outputs ===")
from pydantic import BaseModel

class TestOutput(BaseModel):
    answer: str
    score: int

for model in test_models:
    try:
        response = client.beta.chat.completions.parse(
            model=model,
            messages=[{"role": "user", "content": "Give a test answer"}],
            response_format=TestOutput
        )
        print(f"  ✓ {model}: Structured outputs work!")
    except Exception as e:
        print(f"  ✗ {model}: {str(e)[:60]}")
