import pygame
import sys
import time
from board import (
    BoardState, Direction, InfiniteLoopError
)
import board_io
import visualizer as vis

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 play.py <level_id>")
        return
    
    level_id = sys.argv[1]
    try:
        with open(f"questions/{level_id}.txt", "r") as f:
            initial_state = board_io.parse_board(f.read())
    except Exception as e:
        print(f"Error loading level {level_id}: {e}")
        return

    pygame.init()
    # Calculate window size based on level dimensions
    W_WIDTH = vis.TILE_SIZE * initial_state.setup.width + vis.MARGIN * 2
    W_HEIGHT = vis.TILE_SIZE * initial_state.setup.height + vis.MARGIN * 2
    
    # Extra space for status and controls
    screen = pygame.display.set_mode((max(W_WIDTH, 400), W_HEIGHT + 140))
    pygame.display.set_caption(f"Quell Play - {level_id}")
    clock = pygame.time.Clock()

    current_state = initial_state
    selected_droplet_idx = 0
    status_msg = ""
    status_msg_time = 0

    running = True
    while running:
        now = time.time()
        
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    current_state = initial_state
                    selected_droplet_idx = 0
                    status_msg = "Level Reset"
                    status_msg_time = now
                elif event.key == pygame.K_TAB:
                    if current_state.droplets:
                        selected_droplet_idx = (selected_droplet_idx + 1) % len(current_state.droplets)
                
                # Movement
                elif not current_state.is_solved():
                    direction = None
                    if event.key == pygame.K_UP: direction = Direction.UP
                    elif event.key == pygame.K_DOWN: direction = Direction.DOWN
                    elif event.key == pygame.K_LEFT: direction = Direction.LEFT
                    elif event.key == pygame.K_RIGHT: direction = Direction.RIGHT
                    
                    if direction and current_state.droplets:
                        try:
                            next_state = current_state.get_next_state(selected_droplet_idx, direction)
                            if next_state is None:
                                status_msg = "Droplet Destroyed!"
                                status_msg_time = now
                            else:
                                current_state = next_state
                                # Ensure selection is still valid after merges
                                if not current_state.droplets:
                                    selected_droplet_idx = 0
                                else:
                                    selected_droplet_idx = min(selected_droplet_idx, len(current_state.droplets) - 1)
                                status_msg = ""
                        except InfiniteLoopError:
                            status_msg = "Will goto infinite"
                            status_msg_time = now

        # 2. Draw
        vis.draw_board(screen, current_state)
        
        # Highlight selected droplet
        if current_state.droplets:
            d = current_state.droplets[selected_droplet_idx]
            px, py = vis.get_pixel_pos(d.loc)
            pygame.draw.rect(screen, (255, 255, 255), (px, py, vis.TILE_SIZE, vis.TILE_SIZE), 3)

        # Status Overlay
        status_area_y = W_HEIGHT + 10
        pygame.draw.rect(screen, (30, 30, 30), (0, status_area_y - 10, screen.get_width(), 150))
        
        game_status = "SOLVED!" if current_state.is_solved() else "Playing..."
        color = (0, 255, 0) if current_state.is_solved() else (200, 200, 200)
        status_img = pygame.font.SysFont(None, 28, bold=True).render(game_status, True, color)
        screen.blit(status_img, (vis.MARGIN, status_area_y))
        
        # Temporary status messages (warnings)
        if status_msg and now - status_msg_time < 2.0:
            msg_img = pygame.font.SysFont(None, 24).render(status_msg, True, (255, 100, 100))
            screen.blit(msg_img, (screen.get_width() - vis.MARGIN - msg_img.get_width(), status_area_y))

        # Controls
        ctrl_font = pygame.font.SysFont(None, 20)
        controls = [
            "ARROWS: Move selected Droplet",
            "TAB: Cycle selected Droplet (White box)",
            "R: Reset Level",
            "ESC: Quit"
        ]
        for i, line in enumerate(controls):
            screen.blit(ctrl_font.render(line, True, (150, 150, 150)), (vis.MARGIN, status_area_y + 40 + i * 20))
            
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
