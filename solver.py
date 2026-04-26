import heapq
import time
import json
import sys
import os
from typing import List, Tuple, Optional, Dict
from board import BoardState, Direction
import board_io

def solve(initial_state: BoardState, max_visited: int = 100000) -> Tuple[Optional[List[Dict]], int, float]:
    start_time = time.time()
    
    if initial_state.is_solved():
        return [], 0, time.time() - start_time

    counter = 0
    # (g, h, counter, state)
    pq = [(0, -initial_state.get_droplet_count(), counter, initial_state)]
    
    initial_id = initial_state.get_id()
    # came_from[state_id] = (parent_id, move)
    came_from = {initial_id: None}
    
    nodes_expanded = 0
    final_state = None
    max_g = 0

    while pq:
        if len(came_from) >= max_visited:
            sys.stdout.write(f"\nMax visited states ({max_visited}) reached. Aborting.\n")
            sys.stdout.flush()
            break

        g, h, _, curr_state = heapq.heappop(pq)
        nodes_expanded += 1
        curr_id = curr_state.get_id()

        if g > max_g:
            max_g = g
            sys.stdout.write(f"\rSearching depth: {max_g} | Nodes expanded: {nodes_expanded}   ")
            sys.stdout.flush()
        elif nodes_expanded % 1000 == 0:
            sys.stdout.write(f"\rSearching depth: {max_g} | Nodes expanded: {nodes_expanded}   ")
            sys.stdout.flush()

        if curr_state.is_solved():
            final_state = curr_state
            sys.stdout.write("\n")
            break

        # Try all possible moves
        for droplet_idx in range(len(curr_state.droplets)):
            for direction in Direction:
                result = curr_state.get_next_state(droplet_idx, direction, include_intermediates=False)
                if result is None:
                    continue
                
                next_state, _ = result
                state_id = next_state.get_id()
                if state_id not in came_from:
                    move = {
                        "droplet_idx": droplet_idx,
                        "direction": direction.name,
                        "from": curr_state.droplets[droplet_idx].loc.to_tuple()
                    }
                    came_from[state_id] = (curr_id, move)
                    
                    new_g = g + 1
                    new_h = -next_state.get_droplet_count()
                    counter += 1
                    heapq.heappush(pq, (new_g, new_h, counter, next_state))
    
    if final_state:
        # Reconstruct path
        path = []
        temp_id = final_state.get_id()
        while temp_id != initial_id:
            parent_id, move = came_from[temp_id]
            path.append(move)
            temp_id = parent_id
        path.reverse()
        end_time = time.time()
        return path, len(came_from), end_time - start_time

    end_time = time.time()
    return None, len(came_from), end_time - start_time

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Quell Solver")
    parser.add_argument("level_id", help="Level ID or file path. Use '-' for stdin.")
    parser.add_argument("--record", action="store_true", help="Record the solution to solutions/ folder")
    parser.add_argument("--max-visited", type=int, default=1000000, help="Max visited states before aborting")
    args = parser.parse_args()

    level_id = args.level_id
    if level_id == "-":
        content = sys.stdin.read()
        level_name = "stdin"
    else:
        # Assume levels are in questions/
        if not level_id.endswith(".txt"):
            file_path = f"questions/{level_id}.txt"
            level_name = level_id
        else:
            file_path = level_id
            level_name = os.path.basename(file_path).replace(".txt", "")
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            print(f"Error loading board from {file_path}: {e}")
            return

    try:
        initial_state = board_io.parse_board(content)
    except Exception as e:
        print(f"Error parsing board: {e}")
        return

    solution, visited_count, duration = solve(initial_state, max_visited=args.max_visited)

    result = {}
    if solution is None:
        result = {
            "error": "No solution found",
            "visited": visited_count,
            "time": f"{duration:.4f}s"
        }
    else:
        result = {
            "solution": solution,
            "visited": visited_count,
            "time": f"{duration:.4f}s",
            "steps": len(solution)
        }
    
    print(json.dumps(result, indent=2))

    if args.record and level_name != "stdin":
        os.makedirs("solutions", exist_ok=True)
        record_path = f"solutions/{level_name}.json"
        record_data = {
            "level_id": level_name,
            "steps": len(solution) if solution is not None else None,
            "visited": visited_count,
            "solution": solution
        }
        with open(record_path, "w") as f:
            json.dump(record_data, f, indent=2)
        print(f"Recorded to {record_path}")

if __name__ == "__main__":
    main()
