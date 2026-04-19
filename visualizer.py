import pygame
from board import (
    StationaryPieceType, Loc, StationaryPiece
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
