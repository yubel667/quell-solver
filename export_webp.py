import os
import sys
import time
import json
import pygame
from PIL import Image
import board_io
from board import BoardState, Direction
from solver import solve
import visualizer as vis

# Offscreen rendering
os.environ['SDL_VIDEODRIVER'] = 'dummy'

FPS = 30
INTERP_FRAMES = 5  # Frames between each intermediate state
STEP_DELAY_FRAMES = 15 # Delay after each move
INITIAL_PAUSE_FRAMES = 30
FINAL_PAUSE_FRAMES = 60

def surface_to_pil(surface):
    raw_str = pygame.image.tobytes(surface, "RGB")
    return Image.frombytes("RGB", surface.get_size(), raw_str)

def export_webp(level_id):
    pygame.init()
    
    if not level_id.endswith(".txt"):
        file_path = f"questions/{level_id}.txt"
        level_name = level_id
    else:
        file_path = level_id
        level_name = os.path.basename(file_path).replace(".txt", "")

    try:
        with open(file_path, 'r') as f:
            content = f.read()
        initial_state = board_io.parse_board(content)
    except Exception as e:
        print(f"Error loading level: {e}")
        return

    # Try to load existing solution if available
    sol_path = f"solutions/{level_name}.json"
    solution = None
    if os.path.exists(sol_path):
        try:
            with open(sol_path, 'r') as f:
                data = json.load(f)
                solution = data.get("solution")
                if solution is None and data.get("steps") is not None:
                    # Old format or error
                    solution = None
        except:
            pass

    if solution is None:
        print(f"Solving {level_name}...")
        solution, _, _ = solve(initial_state)
        if solution is None:
            print(f"No solution found for {level_name}")
            return

    print(f"Generating frames for {level_name} ({len(solution)} steps)...")

    W_WIDTH = vis.TILE_SIZE * initial_state.setup.width + vis.MARGIN * 2
    W_HEIGHT = vis.TILE_SIZE * initial_state.setup.height + vis.MARGIN * 2
    surface = pygame.Surface((W_WIDTH, W_HEIGHT + 40))
    font = pygame.font.SysFont(None, 24)
    
    frames = []
    
    def add_frame(state1, state2=None, alpha=0.0, step_num=0):
        if state2:
            vis.draw_board_interpolated(surface, state1, state2, alpha)
        else:
            vis.draw_board(surface, state1)
        
        # UI area
        status_y = W_HEIGHT
        pygame.draw.rect(surface, (30, 30, 30), (0, status_y, W_WIDTH, 40))
        
        status = "SOLVED!" if (step_num == len(solution) and state1.is_solved()) else "Solving..."
        color = (0, 255, 0) if status == "SOLVED!" else (200, 200, 200)
        move_text = f"Step {step_num}/{len(solution)}"
        img = font.render(f"{status} ({move_text})", True, color)
        surface.blit(img, (vis.MARGIN, status_y + 10))
        
        frames.append(surface_to_pil(surface))

    # 1. Initial pause
    for _ in range(INITIAL_PAUSE_FRAMES):
        add_frame(initial_state, step_num=0)

    curr_state = initial_state
    for i, move in enumerate(solution):
        direction = Direction[move["direction"]]
        droplet_idx = move["droplet_idx"]
        
        result = curr_state.get_next_state(droplet_idx, direction, include_intermediates=True)
        if not result:
            print(f"Error: Step {i+1} failed during export simulation!")
            break
        
        next_state, intermediates = result
        
        # Animate through intermediates
        for j in range(len(intermediates) - 1):
            s1 = intermediates[j]
            s2 = intermediates[j+1]
            for f in range(INTERP_FRAMES):
                alpha = f / float(INTERP_FRAMES)
                add_frame(s1, s2, alpha, step_num=i+1)
        
        # Final state of this move
        curr_state = next_state
        for _ in range(STEP_DELAY_FRAMES):
            add_frame(curr_state, step_num=i+1)

    # 2. Final pause
    for _ in range(FINAL_PAUSE_FRAMES):
        add_frame(curr_state, step_num=len(solution))

    # Save WebP
    os.makedirs("solutions_webp", exist_ok=True)
    out_path = f"solutions_webp/{level_name}.webp"
    
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / FPS),
        loop=0,
        quality=80,
        method=6
    )
    
    print(f"Exported to {out_path}")
    pygame.quit()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 export_webp.py <level_id>")
    else:
        export_webp(sys.argv[1])
