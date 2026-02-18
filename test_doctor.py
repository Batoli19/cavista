import sys
import os
sys.path.append(os.getcwd())

from engine.models import Task, Project
from engine.analytics import diagnose_project, calculate_critical_path

def test_doctor():
    print("Testing Project Doctor 🩺...")
    
    # 1. Create a healthy project
    t1 = Task(id="t1", name="Scope", duration_days=1, status="done")
    t2 = Task(id="t2", name="Design", duration_days=2, depends_on=["t1"], status="pending")
    p_healthy = Project(id="p1", name="Healthy Project", tasks=[t1, t2])
    
    diags = diagnose_project(p_healthy.__dict__)
    print(f"\n[Healthy Project]: {diags[0]}")
    assert "healthy" in diags[0].lower()

    # 2. Create a sick project (Delayed Critical Path)
    # T1 is done but took extra time? No, delay_days is added to duration
    t3 = Task(id="t3", name="Critical Task", duration_days=2, delay_days=5, status="pending")
    p_sick = Project(id="p2", name="Sick Project", tasks=[t3])
    
    diags_sick = diagnose_project(p_sick.__dict__)
    print(f"\n[Sick Project]:")
    for d in diags_sick:
        print(f"- {d}")
    
    assert any("delayed by 5 days" in d for d in diags_sick)
    
    # 3. Critical Path Calculation
    # T1 -> T2 -> T3
    task_a = {"id": "a", "duration_days": 1, "depends_on": []}
    task_b = {"id": "b", "duration_days": 1, "depends_on": ["a"]}
    task_c = {"id": "c", "duration_days": 1, "depends_on": ["b"]}
    # Side task
    task_d = {"id": "d", "duration_days": 1, "depends_on": []}
    
    tasks = [task_a, task_b, task_c, task_d]
    cp = calculate_critical_path(tasks)
    print(f"\n[Critical Path]: {cp}")
    
    # Expected: a, b, c should be on it presumably, or at least c since it ends last
    # Our simple logic finds slack=0.
    
    print("\nTest Complete.")

if __name__ == "__main__":
    test_doctor()
