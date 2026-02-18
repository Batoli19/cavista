
import sys
import os
sys.path.append(os.getcwd())

from main import handle_command
import time

print("--- TESTING OPEN NOTEPAD ---")
result = handle_command("Open Notepad")
print(f"Result: {result}")

print("\n--- WAITING 2 SECONDS ---")
time.sleep(2)

print("\n--- TESTING CLOSE NOTEPAD ---")
result = handle_command("Close Notepad")
print(f"Result: {result}")

print("\n--- TESTING OPEN CALCULATOR ---")
result = handle_command("Open Calculator")
print(f"Result: {result}")

print("\n--- TESTING CLOSE CALCULATOR ---")
result = handle_command("Close Calculator")
print(f"Result: {result}")

print("\n--- TESTING OPEN NONEXISTENT APP ---")
result = handle_command("Open FakeApp123")
print(f"Result: {result}")
