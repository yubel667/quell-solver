import pygame
import sys
import os
import numpy as np
import json
from board import (
    BoardState, BoardSetup, Loc, Droplet, Box, Pearl, Portal, Gate, StationaryPieceType, Direction, GoldenWall
)
import board_io
import visualizer as vis

class LevelEditor:
    SIDEBAR_W = 400

    def __init__(self, level_id):
        self.level_id = level_id
        self.file_path = f"questions/{level_id}.txt"
        
        # Grid state
        self.width = 10
        self.height = 10
        self.grid = np.zeros((self.height, self.width), dtype=np.int8)
        self.portals = []
        self.droplets = []
        self.boxes = []
        self.pearls = []
        self.gates = []
        self.golden_walls = []
        self.global_direction = Direction.RIGHT
        
        # Editor state
        self.selected_tool = "WALL"
        self.current_portal_id = "1"
        self.tool_rows = [
            ["DROPLET", "GOLDEN_DROPLET"],
            ["PEARL", "GOLDEN_PEARL"],
            ["WALL", "GOLDEN_WALL"],
            ["BOX"],
            ["SPIKE_UP", "SPIKE_OMNI"],
            ["BUTTON", "ROTATABLE_SPIKE"],
            ["PORTAL"],
            ["GATE_OPEN", "GATE_CLOSED"],
            ["EMPTY", "VOID"]
        ]
        # Flatten tools for indexing (PgUp/Dn)
        self.tools = [t for row in self.tool_rows for t in row]
        
        if os.path.exists(self.file_path):
            self.load()

    def load(self):
        try:
            with open(self.file_path, "r") as f:
                state = board_io.parse_board(f.read())
                self.grid = state.setup.grid
                self.height, self.width = self.grid.shape
                self.portals = state.setup.portals
                self.droplets = state.droplets
                self.boxes = state.boxes
                self.pearls = state.pearls
                self.gates = state.gates
                self.golden_walls = state.golden_walls
                self.global_direction = state.global_direction
        except Exception as e:
            print(f"Error loading level: {e}")

    def save(self):
        try:
            setup = BoardSetup(self.grid, self.portals)
            state = BoardState(setup, self.droplets, self.boxes, self.pearls, self.gates, self.golden_walls, global_direction=self.global_direction)
            os.makedirs("questions", exist_ok=True)
            with open(self.file_path, "w") as f:
                f.write(board_io.serialize_board(state))
            print(f"Saved to {self.file_path}")
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    def resize_grid(self, dw, dh):
        new_w = max(1, self.width + dw)
        new_h = max(1, self.height + dh)
        new_grid = np.zeros((new_h, new_w), dtype=np.int8)
        rh = min(self.height, new_h)
        rw = min(self.width, new_w)
        new_grid[:rh, :rw] = self.grid[:rh, :rw]
        self.grid = new_grid
        self.width = new_w
        self.height = new_h
        self.portals = [p for p in self.portals if p.loc.x < new_w and p.loc.y < new_h]
        self.droplets = [d for d in self.droplets if d.loc.x < new_w and d.loc.y < new_h]
        self.boxes = [b for b in self.boxes if b.loc.x < new_w and b.loc.y < new_h]
        self.pearls = [p for p in self.pearls if p.loc.x < new_w and p.loc.y < new_h]
        self.gates = [g for g in self.gates if g.loc.x < new_w and g.loc.y < new_h]
        self.golden_walls = [w for w in self.golden_walls if w.loc.x < new_w and w.loc.y < new_h]

    def handle_click(self, pos, button, is_drag=False, tile_size=None):
        if tile_size is None: tile_size = vis.TILE_SIZE
        sidebar_x = pygame.display.get_surface().get_width() - self.SIDEBAR_W
        if pos[0] >= sidebar_x:
            if button == 1 and not is_drag:
                y_off = 20
                for row in self.tool_rows:
                    x_off = 20
                    for tool in row:
                        rect = pygame.Rect(sidebar_x + x_off, y_off, 120, 25)
                        if rect.collidepoint(pos):
                            self.selected_tool = tool
                            return
                        x_off += 130
                    y_off += 30
            return

        x = (pos[0] - vis.MARGIN) // tile_size
        y = (pos[1] - vis.MARGIN) // tile_size
        if not (0 <= x < self.width and 0 <= y < self.height): return
        loc = Loc(y, x)
        
        if button == 1: # Add
            # To avoid spamming dynamic entities during drag, check if one already exists
            if is_drag and self._get_any_entity_at(loc): return

            self.remove_entity_at(loc)
            if self.selected_tool == "WALL": self.grid[y, x] = StationaryPieceType.WALL.value
            elif self.selected_tool == "BUTTON": self.grid[y, x] = StationaryPieceType.BUTTON.value
            elif self.selected_tool == "ROTATABLE_SPIKE": self.grid[y, x] = StationaryPieceType.ROTATABLE_SPIKE.value
            elif self.selected_tool.startswith("SPIKE"): self.grid[y, x] = getattr(StationaryPieceType, self.selected_tool).value
            elif self.selected_tool == "EMPTY": self.grid[y, x] = StationaryPieceType.EMPTY.value
            elif self.selected_tool == "VOID": self.grid[y, x] = StationaryPieceType.VOID.value
            elif self.selected_tool == "DROPLET": self.droplets.append(Droplet(loc))
            elif self.selected_tool == "GOLDEN_DROPLET": self.droplets.append(Droplet(loc, is_golden=True))
            elif self.selected_tool == "BOX": self.boxes.append(Box(loc))
            elif self.selected_tool == "PEARL": self.pearls.append(Pearl(loc))
            elif self.selected_tool == "GOLDEN_PEARL": self.pearls.append(Pearl(loc, is_golden=True))
            elif self.selected_tool == "GOLDEN_WALL": self.golden_walls.append(GoldenWall(loc))
            elif self.selected_tool == "PORTAL": self.portals.append(Portal(loc, self.current_portal_id))
            elif self.selected_tool == "GATE_OPEN": self.gates.append(Gate(loc, is_closed=False))
            elif self.selected_tool == "GATE_CLOSED": self.gates.append(Gate(loc, is_closed=True))
        elif button == 3: # Remove
            self.remove_entity_at(loc)
            self.grid[y, x] = StationaryPieceType.EMPTY.value

    def _get_any_entity_at(self, loc):
        for coll in [self.portals, self.droplets, self.boxes, self.pearls, self.gates, self.golden_walls]:
            if any(e.loc == loc for e in coll): return True
        return False

    def remove_entity_at(self, loc):
        self.portals = [p for p in self.portals if not p.loc == loc]
        self.droplets = [d for d in self.droplets if not d.loc == loc]
        self.boxes = [b for b in self.boxes if not b.loc == loc]
        self.pearls = [p for p in self.pearls if not p.loc == loc]
        self.gates = [g for g in self.gates if not g.loc == loc]
        self.golden_walls = [w for w in self.golden_walls if not w.loc == loc]

    def rotate_at(self, loc):
        stat = StationaryPieceType(self.grid[loc.y, loc.x])
        if stat in [StationaryPieceType.SPIKE_UP, StationaryPieceType.SPIKE_DOWN, 
                    StationaryPieceType.SPIKE_LEFT, StationaryPieceType.SPIKE_RIGHT]:
            rot = {StationaryPieceType.SPIKE_UP: StationaryPieceType.SPIKE_RIGHT,
                   StationaryPieceType.SPIKE_RIGHT: StationaryPieceType.SPIKE_DOWN,
                   StationaryPieceType.SPIKE_DOWN: StationaryPieceType.SPIKE_LEFT,
                   StationaryPieceType.SPIKE_LEFT: StationaryPieceType.SPIKE_UP}
            self.grid[loc.y, loc.x] = rot[stat].value
        elif stat == StationaryPieceType.BUTTON:
            # Cycle global direction
            dirs = [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]
            idx = dirs.index(self.global_direction)
            self.global_direction = dirs[(idx + 1) % len(dirs)]
        for g in self.gates:
            if g.loc == loc: g.is_closed = not g.is_closed

    def get_scaled_params(self, screen_w, screen_h, sidebar_w):
        play_area_w = screen_w - sidebar_w
        play_area_h = screen_h
        
        # Calculate tile size that fits the grid
        tile_w = (play_area_w - vis.MARGIN * 2) // self.width
        tile_h = (play_area_h - vis.MARGIN * 2) // self.height
        tile_size = max(10, min(tile_w, tile_h, 60)) # Cap at 60, min 10
        
        return tile_size

    def run(self):
        pygame.init()
        base_w = 800
        base_h = 800
        screen = pygame.display.set_mode((base_w + self.SIDEBAR_W, base_h))
        pygame.display.set_caption(f"Quell Level Editor - {self.level_id}")
        clock = pygame.time.Clock()
        
        font = pygame.font.SysFont(None, 24)
        
        while True:
            screen.fill((50, 50, 50))
            
            tile_size = self.get_scaled_params(screen.get_width(), screen.get_height(), self.SIDEBAR_W)
            # Temporarily override visualizer tile size for drawing
            old_tile_size = vis.TILE_SIZE
            vis.TILE_SIZE = tile_size
            
            setup = BoardSetup(self.grid, self.portals)
            state = BoardState(setup, self.droplets, self.boxes, self.pearls, self.gates, self.golden_walls, global_direction=self.global_direction)
            vis.draw_board(screen, state)
            
            vis.TILE_SIZE = old_tile_size # Restore

            sidebar_x = screen.get_width() - self.SIDEBAR_W
            sidebar_rect = pygame.Rect(sidebar_x, 0, self.SIDEBAR_W, screen.get_height())
            pygame.draw.rect(screen, (30, 30, 30), sidebar_rect)
            
            y_off = 20
            for row in self.tool_rows:
                x_off = 20
                for tool in row:
                    color = (255, 255, 0) if self.selected_tool == tool else (200, 200, 200)
                    screen.blit(font.render(tool, True, color), (sidebar_rect.x + x_off, y_off))
                    x_off += 130
                y_off += 30
            
            y_off += 20
            screen.blit(font.render(f"Portal ID: {self.current_portal_id}", True, (255, 255, 255)), (sidebar_rect.x + 20, y_off))
            y_off += 40
            instructions = ["Drag: Draw/Erase", "R: Rotate/Toggle", "S: Save & Exit", "ESC: Exit", "Arrows: Resize Grid", "1-9: Portal ID", "PgUp/Dn: Cycle Tools"]
            for inst in instructions:
                screen.blit(font.render(inst, True, (150, 150, 150)), (sidebar_rect.x + 20, y_off))
                y_off += 25
            
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos, event.button, is_drag=False, tile_size=tile_size)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    elif event.key == pygame.K_s:
                        if self.save(): return
                    elif event.key == pygame.K_r:
                        m_pos = pygame.mouse.get_pos()
                        x, y = (m_pos[0]-vis.MARGIN)//tile_size, (m_pos[1]-vis.MARGIN)//tile_size
                        if 0<=x<self.width and 0<=y<self.height: self.rotate_at(Loc(y,x))
                    elif event.key == pygame.K_UP: self.resize_grid(0, -1)
                    elif event.key == pygame.K_DOWN: self.resize_grid(0, 1)
                    elif event.key == pygame.K_LEFT: self.resize_grid(-1, 0)
                    elif event.key == pygame.K_RIGHT: self.resize_grid(1, 0)
                    elif pygame.K_1 <= event.key <= pygame.K_9: self.current_portal_id = chr(event.key)
                    elif event.key in [pygame.K_PAGEUP, pygame.K_PAGEDOWN]:
                        idx = self.tools.index(self.selected_tool)
                        self.selected_tool = self.tools[(idx + (1 if event.key == pygame.K_PAGEDOWN else -1)) % len(self.tools)]

            btns = pygame.mouse.get_pressed()
            if btns[0]: self.handle_click(pygame.mouse.get_pos(), 1, is_drag=True, tile_size=tile_size)
            elif btns[2]: self.handle_click(pygame.mouse.get_pos(), 3, is_drag=True, tile_size=tile_size)
            
            clock.tick(60)

if __name__ == "__main__":
    level_id = sys.argv[1] if len(sys.argv) > 1 else "new_level"
    LevelEditor(level_id).run()
