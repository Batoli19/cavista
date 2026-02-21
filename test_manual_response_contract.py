from main import handle_command


def check(cmd: str) -> None:
    result = handle_command(cmd)
    required = {"say_text", "show_text", "evidence", "actions", "meta"}
    missing = required.difference(result.keys()) if isinstance(result, dict) else required
    print(f"Command: {cmd}")
    print(f"Type: {type(result).__name__}")
    print(f"Missing keys: {sorted(missing)}")
    if isinstance(result, dict):
        print(f"say_text: {result.get('say_text', '')}")
        print(f"show_text: {result.get('show_text', '')[:180]}")
        print(f"evidence_count: {len(result.get('evidence', []))}")
        print(f"actions_count: {len(result.get('actions', []))}")
    print("-" * 60)


if __name__ == "__main__":
    check("hello")
    check("make a project workflow")
    check("create a work plan automation plan for this health company with web research")
