import pygame
import time
from board import (
    StationaryPieceType, Loc, StationaryPiece, Direction
)

# Visual Constants
BACKGROUND = (220, 220, 220)  # Light Gray
GRID_LINE_COLOR = (180, 180, 180)
TILE_SIZE = 60
MARGIN = 40

def get_pixel_pos(loc: Loc):
    return MARGIN + loc.x * TILE_SIZE, MARGIN + loc.y * TILE_SIZE

def draw_board(screen, state):
    screen.fill(BACKGROUND)
    
    # Grid lines
    for y in range(state.setup.height + 1):
        pygame.draw.line(screen, GRID_LINE_COLOR, 
                         (MARGIN, MARGIN + y * TILE_SIZE), 
                         (MARGIN + state.setup.width * TILE_SIZE, MARGIN + y * TILE_SIZE))
    for x in range(state.setup.width + 1):
        pygame.draw.line(screen, GRID_LINE_COLOR, 
                         (MARGIN + x * TILE_SIZE, MARGIN), 
                         (MARGIN + x * TILE_SIZE, MARGIN + state.setup.height * TILE_SIZE))
        
    # Draw stationary
    for y in range(state.setup.height):
        for x in range(state.setup.width):
            px, py = get_pixel_pos(Loc(y, x))
            StationaryPiece.render(screen, state.setup.get_stationary_at(Loc(y, x)), px, py, TILE_SIZE)
            
    # Draw portals (part of setup)
    for portal in state.setup.portals:
        px, py = get_pixel_pos(portal.loc)
        portal.render(screen, px, py, TILE_SIZE)
        
    # Draw dynamic entities
    for p in state.pearls:
        px, py = get_pixel_pos(p.loc)
        p.render(screen, px, py, TILE_SIZE)
    for g in state.gates:
        px, py = get_pixel_pos(g.loc)
        g.render(screen, px, py, TILE_SIZE)
    for b in state.boxes:
        px, py = get_pixel_pos(b.loc)
        b.render(screen, px, py, TILE_SIZE)
    for d in state.droplets:
        px, py = get_pixel_pos(d.loc)
        d.render(screen, px, py, TILE_SIZE)

def run_visualizer(initial_state, solution, autoplay=False, show_controls=True, level_id=None):
    pygame.init()
    W_WIDTH = TILE_SIZE * initial_state.setup.width + MARGIN * 2
    W_HEIGHT = TILE_SIZE * initial_state.setup.height + MARGIN * 2
    screen = pygame.display.set_mode((max(W_WIDTH, 400), W_HEIGHT + 140))
    pygame.display.set_caption(f"Quell Visualizer - {level_id}")
    clock = pygame.time.Clock()

    # Pre-calculate all frames for the solution
    # steps_frames is a list of lists of BoardState
    steps_frames = [[initial_state]]
    curr = initial_state
    if solution:
        for move in solution:
            result = curr.get_next_state(move['droplet_idx'], Direction[move['direction']])
            if result:
                final_state, intermediates = result
                # Intermediates[0] is current state, Intermediates[1:] are sliding frames
                steps_frames.append(intermediates[1:])
                curr = final_state

    running = True
    step_idx = 0
    frame_in_step = 0
    paused = not autoplay
    last_frame_time = time.time()
    
    FRAME_DELAY = 0.05      # Sliding animation speed
    STEP_DELAY = 0.5        # Delay between logical moves
    
    in_step_delay = False

    while running:
        now = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                elif event.key == pygame.K_SPACE: 
                    paused = not paused
                    in_step_delay = False
                elif event.key == pygame.K_RIGHT: 
                    # Go to next logical step
                    if step_idx < len(steps_frames) - 1:
                        step_idx += 1
                        frame_in_step = len(steps_frames[step_idx]) - 1
                    paused = True
                elif event.key == pygame.K_LEFT: 
                    # Go to previous logical step
                    if step_idx > 0:
                        step_idx -= 1
                        frame_in_step = len(steps_frames[step_idx]) - 1
                    paused = True
                elif event.key == pygame.K_r: 
                    step_idx = 0
                    frame_in_step = 0
                    paused = True

        # Playback logic
        if not paused:
            elapsed = now - last_frame_time
            if in_step_delay:
                if elapsed >= STEP_DELAY:
                    if step_idx < len(steps_frames) - 1:
                        step_idx += 1
                        frame_in_step = 0
                        in_step_delay = False
                        last_frame_time = now
                    else:
                        paused = True
            else:
                if elapsed >= FRAME_DELAY:
                    if frame_in_step < len(steps_frames[step_idx]) - 1:
                        frame_in_step += 1
                        last_frame_time = now
                    else:
                        # End of current step animation
                        if step_idx < len(steps_frames) - 1:
                            in_step_delay = True
                            last_frame_time = now
                        else:
                            paused = True

        current_frame = steps_frames[step_idx][frame_in_step]
        draw_board(screen, current_frame)
        
        # UI
        status_y = W_HEIGHT + 10
        pygame.draw.rect(screen, (30, 30, 30), (0, status_y - 10, screen.get_width(), 150))
        
        status = "SOLVED!" if current_frame.is_solved() else "Playing..."
        color = (0, 255, 0) if current_frame.is_solved() else (200, 200, 200)
        # step_idx 0 is initial, so moves are 1..N
        move_text = f"Step {step_idx}/{len(steps_frames)-1}"
        img = pygame.font.SysFont(None, 24).render(f"{status} ({move_text})", True, color)
        screen.blit(img, (MARGIN, status_y))

        if show_controls:
            ctrl_font = pygame.font.SysFont(None, 20)
            controls = ["SPACE: Toggle Play/Pause", "RIGHT/LEFT: Next/Prev Step", "R: Reset", "ESC: Quit"]
            for i, line in enumerate(controls):
                screen.blit(ctrl_font.render(line, True, (150, 150, 150)), (MARGIN, status_y + 40 + i * 20))
        
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
