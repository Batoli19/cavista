
import os

# Manually load .env for testing
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    print(f"Loading .env from {env_path}")
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'): continue
            if '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Debug: Print loaded config (masked)
gemini_key = os.environ.get("GEMINI_API_KEY", "")
groq_key = os.environ.get("GROQ_API_KEY", "")
gemini_model = os.environ.get("LLM_MODEL_NAME", "")
groq_model = os.environ.get("GROQ_MODEL_NAME", "")

print(f"GEMINI_KEY: {gemini_key[:5]}... ({len(gemini_key)} chars)")
print(f"GROQ_KEY: {groq_key[:5]}... ({len(groq_key)} chars)")
print(f"GEMINI_MODEL: {gemini_model}")
print(f"GROQ_MODEL: {groq_model}")

import urllib.request
import json

def list_gemini_models(api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("Available Gemini Models:")
            for m in data.get('models', []):
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    print(f" - {m['name']}")
    except Exception as e:
        print(f"Error listing models: {e}")

print("--- Listing Gemini Models ---")
list_gemini_models(gemini_key)

from engine.ai_planner import generate_plan_ai
from engine.ai_chat import chat_with_ai

print("--- Testing Groq (Planner) ---")
try:
    tasks = generate_plan_ai("Test Project", "A simple test project")
    if tasks and len(tasks) > 0:
        print(f"Success! Generated {len(tasks)} tasks.")
        print(f"First task: {tasks[0].get('name')}")
    else:
        print("Failed to generate tasks (Empty list).")
except Exception as e:
    print(f"Groq Error: {e}")

print("\n--- Testing Gemini (Chat) ---")
try:
    response = chat_with_ai("Hello, are you there?")
    print(f"Gemini Response: {response[:50]}...")
except Exception as e:
    print(f"Gemini Error: {e}")
