import sys
import argparse
import os
import json
import board_io
from solver import solve
from visualizer import run_visualizer

def main():
    parser = argparse.ArgumentParser(description="Quell Solver Visualizer")
    parser.add_argument("level_id", help="Level ID (e.g., q-1928-1-1)")
    parser.add_argument("--autoplay", action="store_true", help="Start in auto-play mode")
    parser.add_argument("--no-controls", action="store_false", dest="show_controls", help="Hide controls text")
    parser.set_defaults(show_controls=True)
    
    args = parser.parse_args()
    
    level_id = args.level_id
    if not level_id.endswith(".txt"):
        file_path = f"questions/{level_id}.txt"
    else:
        file_path = level_id

    if not os.path.exists(file_path):
        print(f"Error: Level file {file_path} not found.")
        return

    try:
        print(f"Loading level from {file_path}...")
        with open(file_path, 'r') as f:
            content = f.read()
        initial_state = board_io.parse_board(content)
    except Exception as e:
        print(f"Error parsing level: {e}")
        return

    print("Searching for solution...")
    solution, visited_count, duration = solve(initial_state)

    level_name = os.path.basename(file_path).replace(".txt", "")

    if solution is None:
        print(f"No solution found. (Visited {visited_count} states in {duration:.4f}s)")
        run_visualizer(initial_state, None, autoplay=False, show_controls=args.show_controls, level_id=level_name)
    else:
        print(f"Found solution in {len(solution)} steps.")
        print(f"States visited: {visited_count}")
        print(f"Search time: {duration:.4f}s")
        print("Opening visualizer...")
        run_visualizer(initial_state, solution, autoplay=args.autoplay, show_controls=args.show_controls, level_id=level_name)

if __name__ == "__main__":
    main()
