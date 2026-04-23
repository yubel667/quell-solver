import pygame
import time
from board import (
    StationaryPieceType, Loc, StationaryPiece, Direction, Entity
)

# Visual Constants
BACKGROUND = (220, 220, 220)  # Light Gray
GRID_LINE_COLOR = (180, 180, 180)
TILE_SIZE = 60
MARGIN = 40

def get_pixel_pos(loc: Loc):
    return MARGIN + loc.x * TILE_SIZE, MARGIN + loc.y * TILE_SIZE

def get_pixel_pos_interpolated(loc1: Loc, loc2: Loc, alpha: float):
    # Handle portal "jumps" and toroidal wrap-around
    # If distance > 1.5 cells, don't interpolate (snap at 0.5)
    # We use 1.5 to distinguish between normal move and any jump (portal or wrap)
    dx = abs(loc1.x - loc2.x)
    dy = abs(loc1.y - loc2.y)
    
    if dx > 1.5 or dy > 1.5:
        return get_pixel_pos(loc2 if alpha > 0.5 else loc1)
    
    x = loc1.x + (loc2.x - loc1.x) * alpha
    y = loc1.y + (loc2.y - loc1.y) * alpha
    return MARGIN + x * TILE_SIZE, MARGIN + y * TILE_SIZE

def draw_board(screen, state):
    screen.fill(BACKGROUND)
    for y in range(state.setup.height + 1):
        pygame.draw.line(screen, GRID_LINE_COLOR, (MARGIN, MARGIN + y * TILE_SIZE), (MARGIN + state.setup.width * TILE_SIZE, MARGIN + y * TILE_SIZE))
    for x in range(state.setup.width + 1):
        pygame.draw.line(screen, GRID_LINE_COLOR, (MARGIN + x * TILE_SIZE, MARGIN), (MARGIN + x * TILE_SIZE, MARGIN + state.setup.height * TILE_SIZE))
    for y in range(state.setup.height):
        for x in range(state.setup.width):
            px, py = get_pixel_pos(Loc(y, x))
            StationaryPiece.render(screen, state.setup.get_stationary_at(Loc(y, x)), px, py, TILE_SIZE, global_direction=state.global_direction)
    for portal in state.setup.portals:
        px, py = get_pixel_pos(portal.loc)
        portal.render(screen, px, py, TILE_SIZE)
    for p in state.pearls:
        px, py = get_pixel_pos(p.loc)
        p.render(screen, px, py, TILE_SIZE)
    for g in state.gates:
        px, py = get_pixel_pos(g.loc)
        g.render(screen, px, py, TILE_SIZE)
    for w in state.golden_walls:
        px, py = get_pixel_pos(w.loc)
        w.render(screen, px, py, TILE_SIZE)
    for h in state.hostile_droplets:
        px, py = get_pixel_pos(h.loc)
        h.render(screen, px, py, TILE_SIZE)
    for b in state.boxes:
        px, py = get_pixel_pos(b.loc)
        b.render(screen, px, py, TILE_SIZE)
    for bs in state.boxes_with_spikes:
        px, py = get_pixel_pos(bs.loc)
        bs.render(screen, px, py, TILE_SIZE)
    for d in state.droplets:
        px, py = get_pixel_pos(d.loc)
        d.render(screen, px, py, TILE_SIZE)

def draw_board_interpolated(screen, state1, state2, alpha):
    screen.fill(BACKGROUND)
    for y in range(state1.setup.height + 1):
        pygame.draw.line(screen, GRID_LINE_COLOR, (MARGIN, MARGIN + y * TILE_SIZE), (MARGIN + state1.setup.width * TILE_SIZE, MARGIN + y * TILE_SIZE))
    for x in range(state1.setup.width + 1):
        pygame.draw.line(screen, GRID_LINE_COLOR, (MARGIN + x * TILE_SIZE, MARGIN), (MARGIN + x * TILE_SIZE, MARGIN + state1.setup.height * TILE_SIZE))
    for y in range(state1.setup.height):
        for x in range(state1.setup.width):
            px, py = get_pixel_pos(Loc(y, x))
            StationaryPiece.render(screen, state1.setup.get_stationary_at(Loc(y, x)), px, py, TILE_SIZE, global_direction=state1.global_direction)
    for portal in state1.setup.portals:
        px, py = get_pixel_pos(portal.loc)
        portal.render(screen, px, py, TILE_SIZE)
    
    # Dynamic entities: Match by UUID
    # We prioritize state2 for existing entities, and state1 for disappearing ones
    s1_entities = {e._uuid: e for e in state1.pearls + state1.gates + state1.boxes + state1.boxes_with_spikes + state1.droplets + state1.golden_walls + state1.hostile_droplets if e._uuid}
    s2_entities = {e._uuid: e for e in state2.pearls + state2.gates + state2.boxes + state2.boxes_with_spikes + state2.droplets + state2.golden_walls + state2.hostile_droplets if e._uuid}
    
    all_uuids = set(s1_entities.keys()) | set(s2_entities.keys())
    
    for uuid in all_uuids:
        e1 = s1_entities.get(uuid)
        e2 = s2_entities.get(uuid)
        
        if e1 and e2:
            px, py = get_pixel_pos_interpolated(e1.loc, e2.loc, alpha)
            e2.render(screen, px, py, TILE_SIZE)
        elif e1:
            # Disappearing entity (e.g. collected pearl, merged droplet)
            # Render at e1.loc, maybe fade? For now just static at e1.loc
            px, py = get_pixel_pos(e1.loc)
            e1.render(screen, px, py, TILE_SIZE)
        elif e2:
            # New entity? Should not happen in intermediate frames
            px, py = get_pixel_pos(e2.loc)
            e2.render(screen, px, py, TILE_SIZE)

# Global font cache to avoid expensive SysFont calls every frame
_FONT_CACHE = {}

def get_font(size, bold=False):
    key = (size, bold)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = pygame.font.SysFont(None, size, bold=bold)
    return _FONT_CACHE[key]

def run_visualizer(initial_state, solution, autoplay=False, show_controls=True, level_id=None):
    pygame.init()
    W_WIDTH = TILE_SIZE * initial_state.setup.width + MARGIN * 2
    W_HEIGHT = TILE_SIZE * initial_state.setup.height + MARGIN * 2
    screen = pygame.display.set_mode((max(W_WIDTH, 400), W_HEIGHT + 140))
    pygame.display.set_caption(f"Quell Visualizer - {level_id}")
    clock = pygame.time.Clock()

    steps_frames = [[initial_state]]
    curr = initial_state
    if solution:
        for move in solution:
            result = curr.get_next_state(move['droplet_idx'], Direction[move['direction']], include_intermediates=True)
            if result:
                final_state, intermediates = result
                steps_frames.append(intermediates)
                curr = final_state

    running = True
    step_idx = 0
    frame_in_step = 0
    frame_alpha = 0.0 # 0.0 to 1.0 between frame_in_step and frame_in_step + 1
    
    paused = not autoplay
    
    ANIM_SPEED = 10.0        # Grid cells per second
    STEP_DELAY = 0.5        # Delay between logical moves

    in_step_delay = False
    delay_start_time = 0
    stop_after_step = False

    last_update_time = time.time()

    while running:
        now = time.time()
        dt = now - last_update_time
        last_update_time = now

        current_frame = steps_frames[step_idx][frame_in_step]
        is_solved = current_frame.is_solved()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                elif event.key in [pygame.K_SPACE, pygame.K_RETURN] and is_solved:
                    running = False
                elif event.key == pygame.K_RETURN:
                    paused = not paused
                    in_step_delay = False
                    stop_after_step = False
                elif event.key == pygame.K_SPACE:
                    # Play NEXT step then stop
                    if step_idx < len(steps_frames) - 1:
                        if frame_in_step == len(steps_frames[step_idx]) - 1:
                            step_idx += 1
                            frame_in_step = 0
                        frame_alpha = 0.0
                        paused = False
                        in_step_delay = False
                        stop_after_step = True
                    else:
                        paused = True
                elif event.key == pygame.K_RIGHT: 
                    if step_idx < len(steps_frames) - 1:
                        step_idx += 1
                        frame_in_step = len(steps_frames[step_idx]) - 1
                        frame_alpha = 0.0
                    paused = True
                    in_step_delay = False
                    stop_after_step = False
                elif event.key == pygame.K_LEFT: 
                    if step_idx > 0:
                        step_idx -= 1
                        frame_in_step = len(steps_frames[step_idx]) - 1
                        frame_alpha = 0.0
                    paused = True
                    in_step_delay = False
                    stop_after_step = False
                elif event.key == pygame.K_r: 
                    step_idx = 0
                    frame_in_step = 0
                    frame_alpha = 0.0
                    paused = True
                    in_step_delay = False
                    stop_after_step = False

        # Playback logic
        if not paused:
            if step_idx == 0:
                # Initial state (Step 0) has no animation, jump to first move immediately
                if len(steps_frames) > 1:
                    step_idx = 1
                    frame_in_step = 0
                    frame_alpha = 0.0
                else:
                    paused = True
            elif in_step_delay:
                if now - delay_start_time >= STEP_DELAY:
                    if step_idx < len(steps_frames) - 1:
                        if stop_after_step:
                            paused = True
                            stop_after_step = False
                        else:
                            step_idx += 1
                            frame_in_step = 0
                            frame_alpha = 0.0
                            in_step_delay = False
                    else:
                        paused = True
            else:
                frame_alpha += dt * ANIM_SPEED
                while frame_alpha >= 1.0:
                    frame_alpha -= 1.0
                    if frame_in_step < len(steps_frames[step_idx]) - 1:
                        frame_in_step += 1
                    else:
                        # End of animation for this step
                        if step_idx < len(steps_frames) - 1:
                            if stop_after_step:
                                paused = True
                                frame_alpha = 0.0 # Snap to end
                                break
                            else:
                                in_step_delay = True
                                delay_start_time = now
                                frame_alpha = 0.0 # Reset for next step
                                break
                        else:
                            paused = True
                            frame_alpha = 0.0 # Snap to end
                            break

        # Rendering
        if not in_step_delay and frame_in_step < len(steps_frames[step_idx]) - 1:
            state1 = steps_frames[step_idx][frame_in_step]
            state2 = steps_frames[step_idx][frame_in_step + 1]
            draw_board_interpolated(screen, state1, state2, frame_alpha)
        else:
            draw_board(screen, steps_frames[step_idx][frame_in_step])
        
        # UI
        status_y = W_HEIGHT + 10
        pygame.draw.rect(screen, (30, 30, 30), (0, status_y - 10, screen.get_width(), 150))
        current_frame = steps_frames[step_idx][frame_in_step]
        status = "SOLVED!" if current_frame.is_solved() else "Playing..."
        color = (0, 255, 0) if current_frame.is_solved() else (200, 200, 200)
        move_text = f"Step {step_idx}/{len(steps_frames)-1}"
        img = get_font(24).render(f"{status} ({move_text})", True, color)
        screen.blit(img, (MARGIN, status_y))

        if show_controls:
            ctrl_font = get_font(20)
            controls = ["ENTER: Toggle Auto-play", "SPACE: Play Next Step", "RIGHT/LEFT: Jump to Step", "R: Reset", "ESC: Quit"]
            for i, line in enumerate(controls):
                screen.blit(ctrl_font.render(line, True, (150, 150, 150)), (MARGIN, status_y + 40 + i * 20))
        
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
