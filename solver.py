import heapq
import time
import json
import sys
from typing import List, Tuple, Optional, Dict
from board import BoardState, Direction, InfiniteLoopError
import board_io

def solve(initial_state: BoardState) -> Tuple[Optional[List[Dict]], int, float]:
    start_time = time.time()
    
    if initial_state.is_solved():
        return [], 0, time.time() - start_time

    # Priority queue stores (g_score, -droplet_count, counter, state, path)
    # g_score = distance from start (ensures shortest path)
    # -droplet_count = heuristic to prefer keeping droplets
    
    counter = 0
    # (g, h, count, state, path)
    pq = [(0, -initial_state.get_droplet_count(), counter, initial_state, [])]
    
    visited = {initial_state.get_id()}
    
    nodes_expanded = 0

    while pq:
        g, h, _, curr_state, path = heapq.heappop(pq)
        nodes_expanded += 1

        if curr_state.is_solved():
            end_time = time.time()
            return path, len(visited), end_time - start_time

        # Try all possible moves
        # Each move is (droplet_index, direction)
        for droplet_idx in range(len(curr_state.droplets)):
            for direction in Direction:
                try:
                    next_state = curr_state.get_next_state(droplet_idx, direction)
                    if next_state is None:
                        continue
                    
                    state_id = next_state.get_id()
                    if state_id not in visited:
                        visited.add(state_id)
                        new_g = g + 1
                        new_h = -next_state.get_droplet_count()
                        
                        move = {
                            "droplet_idx": droplet_idx,
                            "direction": direction.name,
                            "from": curr_state.droplets[droplet_idx].loc.to_tuple()
                        }
                        new_path = path + [move]
                        
                        counter += 1
                        heapq.heappush(pq, (new_g, new_h, counter, next_state, new_path))
                except InfiniteLoopError:
                    continue
    
    end_time = time.time()
    return None, len(visited), end_time - start_time

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 solver.py <level_id>")
        return

    level_id = sys.argv[1]
    if level_id == "-":
        content = sys.stdin.read()
    else:
        # Assume levels are in questions/
        if not level_id.endswith(".txt"):
            file_path = f"quell-solver/questions/{level_id}.txt"
        else:
            file_path = level_id
            
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

    solution, visited_count, duration = solve(initial_state)

    if solution is None:
        print(json.dumps({
            "error": "No solution found",
            "visited": visited_count,
            "time": f"{duration:.4f}s"
        }, indent=2))
    else:
        print(json.dumps({
            "solution": solution,
            "visited": visited_count,
            "time": f"{duration:.4f}s",
            "steps": len(solution)
        }, indent=2))

if __name__ == "__main__":
    main()
