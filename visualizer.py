import pygame
import math
from board import (
    Direction, StationaryPieceType, Loc, Droplet, Box, Pearl, Portal, Gate
)

# Colors
BACKGROUND = (220, 220, 220)  # Light Gray
WALL_COLOR = (60, 60, 60)      # Dark Gray
DROPLET_COLOR = (0, 255, 255)  # Cyan
BOX_COLOR = (139, 69, 19)      # Brown
PEARL_COLOR = (255, 255, 255)  # White
PORTAL_COLOR = (255, 215, 0)   # Yellow/Gold
GATE_COLOR = (0, 200, 0)       # Green
SPIKE_COLOR = (255, 0, 0)      # Red
GRID_LINE_COLOR = (180, 180, 180)

TILE_SIZE = 60
MARGIN = 40

def get_pixel_pos(loc: Loc):
    return MARGIN + loc.x * TILE_SIZE, MARGIN + loc.y * TILE_SIZE

def draw_stationary(screen, stat: StationaryPieceType, loc: Loc):
    px, py = get_pixel_pos(loc)
    rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)
    
    if stat == StationaryPieceType.WALL:
        pygame.draw.rect(screen, WALL_COLOR, rect)
        pygame.draw.rect(screen, (40, 40, 40), rect, 2)
    
    elif stat != StationaryPieceType.EMPTY:
        # Spike base
        pygame.draw.rect(screen, SPIKE_COLOR, rect)
        center = rect.center
        
        if stat == StationaryPieceType.SPIKE_OMNI:
            # Draw a star
            points = []
            for i in range(8):
                angle = i * math.pi / 4
                r = TILE_SIZE // 4 if i % 2 == 0 else TILE_SIZE // 8
                points.append((center[0] + r * math.cos(angle), center[1] + r * math.sin(angle)))
            pygame.draw.polygon(screen, PEARL_COLOR, points)
        else:
            # Draw an arrow
            r = TILE_SIZE // 4
            arrow_map = {
                StationaryPieceType.SPIKE_UP: (0, -r),
                StationaryPieceType.SPIKE_DOWN: (0, r),
                StationaryPieceType.SPIKE_LEFT: (-r, 0),
                StationaryPieceType.SPIKE_RIGHT: (r, 0)
            }
            offset = arrow_map[stat]
            tip = (center[0] + offset[0], center[1] + offset[1])
            # Draw a simple triangle tip
            if stat == StationaryPieceType.SPIKE_UP:
                pts = [tip, (tip[0]-10, tip[1]+15), (tip[0]+10, tip[1]+15)]
            elif stat == StationaryPieceType.SPIKE_DOWN:
                pts = [tip, (tip[0]-10, tip[1]-15), (tip[0]+10, tip[1]-15)]
            elif stat == StationaryPieceType.SPIKE_LEFT:
                pts = [tip, (tip[0]+15, tip[1]-10), (tip[0]+15, tip[1]+10)]
            else: # RIGHT
                pts = [tip, (tip[0]-15, tip[1]-10), (tip[0]-15, tip[1]+10)]
            pygame.draw.polygon(screen, PEARL_COLOR, pts)

def draw_entity(screen, entity):
    px, py = get_pixel_pos(entity.loc)
    center = (px + TILE_SIZE // 2, py + TILE_SIZE // 2)
    
    if isinstance(entity, Droplet):
        pygame.draw.circle(screen, DROPLET_COLOR, center, TILE_SIZE // 2 - 5)
        pygame.draw.circle(screen, (0, 200, 200), center, TILE_SIZE // 2 - 5, 2)
        
    elif isinstance(entity, Box):
        rect = pygame.Rect(px + 5, py + 5, TILE_SIZE - 10, TILE_SIZE - 10)
        pygame.draw.rect(screen, BOX_COLOR, rect)
        pygame.draw.rect(screen, (80, 40, 10), rect, 2)
        
    elif isinstance(entity, Pearl):
        pygame.draw.circle(screen, PEARL_COLOR, center, TILE_SIZE // 4)
        pygame.draw.circle(screen, (200, 200, 200), center, TILE_SIZE // 4, 1)
        
    elif isinstance(entity, Portal):
        pygame.draw.circle(screen, PORTAL_COLOR, center, TILE_SIZE // 2 - 10, 5)
        # Draw ID
        font = pygame.font.SysFont(None, 24)
        img = font.render(str(entity.portal_id), True, WALL_COLOR)
        screen.blit(img, (center[0] - img.get_width() // 2, center[1] - img.get_height() // 2))
        
    elif isinstance(entity, Gate):
        if not entity.is_closed:
            # tiny green circle
            pygame.draw.circle(screen, GATE_COLOR, center, 5)
        else:
            # 9 tiny green circles
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    c = (center[0] + dx * 15, center[1] + dy * 15)
                    pygame.draw.circle(screen, GATE_COLOR, c, 3)

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
            draw_stationary(screen, state.setup.get_stationary_at(Loc(y, x)), Loc(y, x))
            
    # Draw portals (part of setup)
    for portal in state.setup.portals:
        draw_entity(screen, portal)
        
    # Draw dynamic
    for p in state.pearls: draw_entity(screen, p)
    for g in state.gates: draw_entity(screen, g)
    for b in state.boxes: draw_entity(screen, b)
    for d in state.droplets: draw_entity(screen, d)
