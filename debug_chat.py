import os
import sys

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

# Load .env file manually
env_path = os.path.join(os.getcwd(), ".env")
if os.path.exists(env_path):
    print(f"[Debug] Loading environment from {env_path}")
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()

# NO manual override here - we want to test the .env value and the logic in ai_chat.py
print(f"API Key present: {bool(os.environ.get('GEMINI_API_KEY'))}")
print(f"Model Name: {os.environ.get('LLM_MODEL_NAME')}")

from engine.ai_chat import chat_with_ai

print("Testing Chat with AI...")
try:
    response = chat_with_ai("Hello, tell me a one sentence joke.")
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")
