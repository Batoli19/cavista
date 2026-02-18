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

from engine.ai_chat import chat_with_ai

print("-" * 50)
print(f"Current Provider: {os.environ.get('LLM_PROVIDER')}")
print(f"Gemini Key Present: {bool(os.environ.get('GEMINI_API_KEY'))}")
print(f"Groq Key Present: {bool(os.environ.get('GROQ_API_KEY'))}")
print("-" * 50)

# Test 1: Default (should be Gemini)
print("\n--- Test 1: Default Provider (Gemini) ---")
try:
    # Force provider to Gemini for test
    os.environ['LLM_PROVIDER'] = 'gemini'
    # Reload module to pick up env change? No, module globals are set at import.
    # We need to monkey-patch or just rely on the fallback logic being tested via Groq failure if we want.
    # Actually, let's just test what's configured, which is gemini.
    response = chat_with_ai("Test: Answer 'Gemini' if you are Google.")
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Switch to Groq
print("\n--- Test 2: Switch to Groq ---")
try:
    # We must patch the DEFAULT_PROVIDER in the imported module because it's read at import time
    import engine.ai_chat
    engine.ai_chat.DEFAULT_PROVIDER = "groq"
    
    response = chat_with_ai("Test: Answer 'Groq' if you are Llama.")
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Fallback (Groq with Files)
print("\n--- Test 3: Fallback (Files -> Gemini) ---")
try:
    # Provider is still Groq from Test 2 patch
    # But we send a dummy file
    dummy_files = [{"name": "test.txt", "type": "text/plain", "content": "ZHVtbXk="}]
    response = chat_with_ai("Test: Acknowledge receiving a file.", files=dummy_files)
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")
