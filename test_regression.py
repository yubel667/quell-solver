import os
import json
import time
import argparse
from board import Direction
import board_io
from solver import solve

def run_regression(full=False, max_visited=500):
    solutions_dir = "solutions"
    if not os.path.exists(solutions_dir):
        print(f"No solutions directory found at {solutions_dir}")
        return

    files = [f for f in os.listdir(solutions_dir) if f.endswith(".json")]
    files.sort()

    passed = 0
    failed = 0
    skipped = 0

    print(f"Running regression check... (full={full}, max_visited={max_visited})")
    print("-" * 60)

    for filename in files:
        with open(os.path.join(solutions_dir, filename), "r") as f:
            data = json.load(f)

        level_id = data["level_id"]
        expected_steps = data["steps"]
        recorded_visited = data["visited"]

        if not full and recorded_visited > max_visited:
            skipped += 1
            # print(f"Skipping {level_id} (visited {recorded_visited} > {max_visited})")
            continue

        # Load level
        level_path = f"questions/{level_id}.txt"
        if not os.path.exists(level_path):
            print(f"FAILED: Level file {level_path} not found.")
            failed += 1
            continue

        with open(level_path, "r") as f:
            initial_state = board_io.parse_board(f.read())

        # Solve
        start_time = time.time()
        solution, visited, duration = solve(initial_state)
        
        actual_steps = len(solution) if solution is not None else None

        if actual_steps == expected_steps:
            print(f"PASSED: {level_id} | Steps: {actual_steps} | Visited: {visited} | Time: {duration}s")
            passed += 1
        else:
            print(f"FAILED: {level_id} | Expected: {expected_steps} | Actual: {actual_steps} | Visited: {visited}")
            failed += 1

    print("-" * 60)
    print(f"Summary: {passed} passed, {failed} failed, {skipped} skipped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solver Regression Test")
    parser.add_argument("--full", action="store_true", help="Run all tests including slow ones")
    parser.add_argument("--max-visited", type=int, default=5000, help="Max visited states for non-full run")
    args = parser.parse_args()

    run_regression(full=args.full, max_visited=args.max_visited)
