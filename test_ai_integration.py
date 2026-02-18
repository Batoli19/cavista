import os
import sys

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from engine.engine import create_project, generate_plan

def test_fallback():
    print("Testing Fallback Mechanism (No API Key)...")
    # 1. Create Project
    p = create_project("Test Project", description="A simple test project")
    print(f"Created project: {p['name']} ({p['id']})")
    
    # 2. Generate Plan (Should default to basic because no key)
    tasks = generate_plan(p, use_ai=True)
    
    # 3. Verify
    print(f"Generated {len(tasks)} tasks.")
    if len(tasks) == 5 and tasks[0]["id"] == "t1":
        print("SUCCESS: Fallback plan generated correctly.")
    else:
        print("FAILURE: Unexpected plan generated.")
        print(tasks)

if __name__ == "__main__":
    test_fallback()
