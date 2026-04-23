import numpy as np
from typing import List, Tuple, Dict, Optional, Set, Union
import enum
import math
import pygame

class Direction(enum.Enum):
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

class StationaryPieceType(enum.Enum):
    EMPTY = 0
    WALL = 1
    SPIKE_UP = 2
    SPIKE_DOWN = 3
    SPIKE_LEFT = 4
    SPIKE_RIGHT = 5
    SPIKE_OMNI = 6
    BUTTON = 7
    ROTATABLE_SPIKE = 8
    VOID = 9

class Loc:
    def __init__(self, y: int, x: int):
        self.y = y
        self.x = x

    def __add__(self, other: Direction):
        return Loc(self.y + other.value[0], self.x + other.value[1])

    def __eq__(self, other):
        return isinstance(other, Loc) and self.y == other.y and self.x == other.x

    def __hash__(self):
        return hash((self.y, self.x))
    
    def to_tuple(self):
        return (self.y, self.x)

class InfiniteLoopError(Exception):
    pass

class Entity:
    def __init__(self, loc: Loc):
        self.loc = loc
        self._uuid = None

    def clone(self):
        new_e = self.__class__(self.loc)
        new_e._uuid = self._uuid
        return new_e

    def get_sort_key(self) -> Tuple:
        raise NotImplementedError()

    def render(self, screen, px, py, tile_size):
        pass

class Pearl(Entity):
    def __init__(self, loc: Loc, is_golden: bool = False):
        super().__init__(loc)
        self.is_golden = is_golden

    def clone(self):
        new_e = Pearl(self.loc, self.is_golden)
        new_e._uuid = self._uuid
        return new_e

    def get_sort_key(self):
        return ("p", self.loc.y, self.loc.x, self.is_golden)

    def render(self, screen, px, py, tile_size):
        center = (px + tile_size // 2, py + tile_size // 2)
        color = (255, 215, 0) if self.is_golden else (255, 255, 255)
        pygame.draw.circle(screen, color, center, tile_size // 4)
        pygame.draw.circle(screen, (200, 200, 200), center, tile_size // 4, 1)

class Gate(Entity):
    def __init__(self, loc: Loc, is_closed: bool = False):
        super().__init__(loc)
        self.is_closed = is_closed

    def clone(self):
        new_e = Gate(self.loc, self.is_closed)
        new_e._uuid = self._uuid
        return new_e

    def get_sort_key(self):
        return ("g", self.loc.y, self.loc.x, self.is_closed)

    def render(self, screen, px, py, tile_size):
        center = (px + tile_size // 2, py + tile_size // 2)
        color = (0, 200, 0)
        if not self.is_closed:
            pygame.draw.circle(screen, color, center, 5)
        else:
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    c = (center[0] + dx * 15, center[1] + dy * 15)
                    pygame.draw.circle(screen, color, c, 5)

_PORTAL_FONT = None

class Portal(Entity):
    def __init__(self, loc: Loc, portal_id: str):
        super().__init__(loc)
        self.portal_id = portal_id

    def clone(self):
        new_e = Portal(self.loc, self.portal_id)
        new_e._uuid = self._uuid
        return new_e

    def get_sort_key(self):
        return ("o", self.portal_id, self.loc.y, self.loc.x)

    def render(self, screen, px, py, tile_size):
        global _PORTAL_FONT
        center = (px + tile_size // 2, py + tile_size // 2)
        pygame.draw.circle(screen, (255, 215, 0), center, tile_size // 2 - 10, 5)
        if _PORTAL_FONT is None:
            _PORTAL_FONT = pygame.font.SysFont(None, 24)
        img = _PORTAL_FONT.render(str(self.portal_id), True, (60, 60, 60))
        screen.blit(img, (center[0] - img.get_width() // 2, center[1] - img.get_height() // 2))

class Movable(Entity):
    def can_move_into(self, target_entity: Optional[Entity], direction: Direction) -> bool:
        """Returns True if this piece can move into a cell occupied by target_entity."""
        raise NotImplementedError()

    def handle_collision(self, target_entity: Optional[Entity], state: 'SimState') -> bool:
        """Handles the effect of moving into target_entity. Returns True if piece should stop."""
        raise NotImplementedError()

    def is_blocked_by_stationary(self, stat: StationaryPieceType, direction: Direction, global_direction: Optional[Direction] = None) -> bool:
        raise NotImplementedError()

class Droplet(Movable):
    def __init__(self, loc: Loc, is_golden: bool = False):
        super().__init__(loc)
        self.is_golden = is_golden

    def clone(self):
        new_e = Droplet(self.loc, self.is_golden)
        new_e._uuid = self._uuid
        return new_e

    def get_sort_key(self):
        return ("d", self.loc.y, self.loc.x, self.is_golden)

    def render(self, screen, px, py, tile_size):
        center = (px + tile_size // 2, py + tile_size // 2)
        fill_color = (255, 215, 0) if self.is_golden else (0, 255, 255)
        border_color = (184, 134, 11) if self.is_golden else (0, 200, 200)
        pygame.draw.circle(screen, fill_color, center, tile_size // 2 - 5)
        pygame.draw.circle(screen, border_color, center, tile_size // 2 - 5, 2)

    def is_blocked_by_stationary(self, stat: StationaryPieceType, direction: Direction, global_direction: Optional[Direction] = None) -> bool:
        if stat == StationaryPieceType.WALL:
            return True
        if stat in {StationaryPieceType.SPIKE_UP, StationaryPieceType.SPIKE_DOWN, 
                    StationaryPieceType.SPIKE_LEFT, StationaryPieceType.SPIKE_RIGHT}:
            return not self._is_lethal(stat, direction)
        if stat == StationaryPieceType.ROTATABLE_SPIKE and global_direction:
            # Map global_direction to the corresponding SPIKE type
            spike_map = {
                Direction.UP: StationaryPieceType.SPIKE_UP,
                Direction.DOWN: StationaryPieceType.SPIKE_DOWN,
                Direction.LEFT: StationaryPieceType.SPIKE_LEFT,
                Direction.RIGHT: StationaryPieceType.SPIKE_RIGHT
            }
            mapped_spike = spike_map[global_direction]
            return not self._is_lethal(mapped_spike, direction)
        return False

    def handle_stationary_collision(self, stat: StationaryPieceType, direction: Direction, global_direction: Optional[Direction] = None):
        if stat in {StationaryPieceType.SPIKE_UP, StationaryPieceType.SPIKE_DOWN, 
                    StationaryPieceType.SPIKE_LEFT, StationaryPieceType.SPIKE_RIGHT, 
                    StationaryPieceType.SPIKE_OMNI}:
            if self._is_lethal(stat, direction):
                raise ValueError("Droplet Destroyed")
        if stat == StationaryPieceType.ROTATABLE_SPIKE and global_direction:
            spike_map = {
                Direction.UP: StationaryPieceType.SPIKE_UP,
                Direction.DOWN: StationaryPieceType.SPIKE_DOWN,
                Direction.LEFT: StationaryPieceType.SPIKE_LEFT,
                Direction.RIGHT: StationaryPieceType.SPIKE_RIGHT
            }
            mapped_spike = spike_map[global_direction]
            if self._is_lethal(mapped_spike, direction):
                raise ValueError("Droplet Destroyed")

    def _is_lethal(self, stat: StationaryPieceType, direction: Direction) -> bool:
        if stat == StationaryPieceType.SPIKE_OMNI: return True
        return (stat == StationaryPieceType.SPIKE_UP and direction == Direction.DOWN) or \
               (stat == StationaryPieceType.SPIKE_DOWN and direction == Direction.UP) or \
               (stat == StationaryPieceType.SPIKE_LEFT and direction == Direction.RIGHT) or \
               (stat == StationaryPieceType.SPIKE_RIGHT and direction == Direction.LEFT)

    def can_move_into(self, target: Optional[Entity], direction: Direction) -> bool:
        if target is None: return True
        if isinstance(target, (Pearl, Droplet, HostileDroplet)): return True
        if isinstance(target, Box): return True 
        if isinstance(target, BoxWithSpike): return True
        if isinstance(target, Gate): return not target.is_closed
        if isinstance(target, Portal): return True
        return False

    def handle_collision(self, target: Optional[Entity], state: 'SimState'):
        if isinstance(target, Pearl):
            state.pearls.remove(target)
            return False
        if isinstance(target, Droplet):
            state.to_remove.add(target) 
            return False
        if isinstance(target, HostileDroplet):
            state.to_remove.add(self)
            state.to_remove.add(target) 
            return False
        if isinstance(target, Box):
            if target not in state.moving_pieces:
                state.moving_pieces.add(target)
            return False 
        return False

class Box(Movable):
    def get_sort_key(self):
        return ("b", self.loc.y, self.loc.x)

    def render(self, screen, px, py, tile_size):
        rect = pygame.Rect(px + 5, py + 5, tile_size - 10, tile_size - 10)
        pygame.draw.rect(screen, (139, 69, 19), rect)
        pygame.draw.rect(screen, (80, 40, 10), rect, 2)

    def is_blocked_by_stationary(self, stat: StationaryPieceType, direction: Direction, global_direction: Optional[Direction] = None) -> bool:
        if stat == StationaryPieceType.WALL: return True
        if stat in {StationaryPieceType.SPIKE_UP, StationaryPieceType.SPIKE_DOWN, 
                        StationaryPieceType.SPIKE_LEFT, StationaryPieceType.SPIKE_RIGHT, 
                        StationaryPieceType.SPIKE_OMNI}:
            return True
        if stat == StationaryPieceType.ROTATABLE_SPIKE:
            return True
        return False

    def can_move_into(self, target: Optional[Entity], direction: Direction) -> bool:
        if target is None: return True
        if isinstance(target, Gate): return not target.is_closed
        if isinstance(target, Portal): return True
        if isinstance(target, Box): return True 
        return False

    def handle_collision(self, target: Optional[Entity], state: 'SimState'):
        if isinstance(target, Box):
            state.to_remove.add(self)
            state.to_remove.add(target)
            return False
        return False

class BoxWithSpike(Movable):
    def __init__(self, loc: Loc, spike_dir: Direction):
        super().__init__(loc)
        self.spike_dir = spike_dir

    def clone(self):
        new_e = BoxWithSpike(self.loc, self.spike_dir)
        new_e._uuid = self._uuid
        return new_e

    def get_sort_key(self):
        return ("bs", self.loc.y, self.loc.x, self.spike_dir.name)

    def render(self, screen, px, py, tile_size):
        # Brown square like box
        rect = pygame.Rect(px + 5, py + 5, tile_size - 10, tile_size - 10)
        pygame.draw.rect(screen, (139, 69, 19), rect)
        pygame.draw.rect(screen, (80, 40, 10), rect, 2)
        
        # Small red arrow for spike_dir
        center = rect.center
        r = tile_size // 4
        color = (255, 0, 0)
        dy, dx = self.spike_dir.value
        tip = (center[0] + dx * r, center[1] + dy * r)
        if self.spike_dir == Direction.UP: pts = [tip, (tip[0]-10, tip[1]+15), (tip[0]+10, tip[1]+15)]
        elif self.spike_dir == Direction.DOWN: pts = [tip, (tip[0]-10, tip[1]-15), (tip[0]+10, tip[1]-15)]
        elif self.spike_dir == Direction.LEFT: pts = [tip, (tip[0]+15, tip[1]-10), (tip[0]+15, tip[1]+10)]
        else: pts = [tip, (tip[0]-15, tip[1]-10), (tip[0]-15, tip[1]+10)]
        pygame.draw.polygon(screen, color, pts)

    def is_blocked_by_stationary(self, stat: StationaryPieceType, direction: Direction, global_direction: Optional[Direction] = None) -> bool:
        if stat == StationaryPieceType.WALL: return True
        if stat in {StationaryPieceType.SPIKE_UP, StationaryPieceType.SPIKE_DOWN, 
                        StationaryPieceType.SPIKE_LEFT, StationaryPieceType.SPIKE_RIGHT, 
                        StationaryPieceType.SPIKE_OMNI}:
            return True
        if stat == StationaryPieceType.ROTATABLE_SPIKE:
            return True
        return False

    def can_move_into(self, target: Optional[Entity], direction: Direction) -> bool:
        if target is None: return True
        if isinstance(target, Gate): return not target.is_closed
        if isinstance(target, Portal): return True
        if isinstance(target, (Droplet, HostileDroplet)):
            if direction == self.spike_dir:
                return True
            return False
        return False

    def handle_collision(self, target: Optional[Entity], state: 'SimState'):
        return False

class GoldenWall(Entity):
    def clone(self):
        new_e = GoldenWall(self.loc)
        new_e._uuid = self._uuid
        return new_e

    def get_sort_key(self):
        return ("w", self.loc.y, self.loc.x)

    def render(self, screen, px, py, tile_size):
        rect = pygame.Rect(px, py, tile_size, tile_size)
        pygame.draw.rect(screen, (218, 165, 32), rect)
        pygame.draw.rect(screen, (184, 134, 11), rect, 2)

class HostileDroplet(Entity):
    def clone(self):
        new_e = HostileDroplet(self.loc)
        new_e._uuid = self._uuid
        return new_e

    def get_sort_key(self):
        return ("h", self.loc.y, self.loc.x)

    def render(self, screen, px, py, tile_size):
        center = (px + tile_size // 2, py + tile_size // 2)
        pygame.draw.circle(screen, (255, 0, 0), center, tile_size // 2 - 5)
        pygame.draw.circle(screen, (150, 0, 0), center, tile_size // 2 - 5, 2)

class StationaryPiece:
    @staticmethod
    def render(screen, stat: StationaryPieceType, px, py, tile_size, global_direction: Optional[Direction] = Direction.RIGHT):
        rect = pygame.Rect(px, py, tile_size, tile_size)
        if stat == StationaryPieceType.VOID:
            pygame.draw.rect(screen, (0, 0, 0), rect)
        elif stat == StationaryPieceType.WALL:
            pygame.draw.rect(screen, (60, 60, 60), rect)
            pygame.draw.rect(screen, (40, 40, 40), rect, 2)
        elif stat == StationaryPieceType.BUTTON:
            # Button is a small red arrow
            center = rect.center
            r = tile_size // 6
            color = (255, 0, 0)
            if global_direction:
                dy, dx = global_direction.value
                tip = (center[0] + dx * r * 2, center[1] + dy * r * 2)
                # Drawing a simple triangle arrow
                if global_direction == Direction.UP: pts = [tip, (tip[0]-5, tip[1]+10), (tip[0]+5, tip[1]+10)]
                elif global_direction == Direction.DOWN: pts = [tip, (tip[0]-5, tip[1]-10), (tip[0]+5, tip[1]-10)]
                elif global_direction == Direction.LEFT: pts = [tip, (tip[0]+10, tip[1]-5), (tip[0]+10, tip[1]+5)]
                else: pts = [tip, (tip[0]-10, tip[1]-5), (tip[0]-10, tip[1]+5)]
                pygame.draw.polygon(screen, color, pts)
        elif stat in {StationaryPieceType.SPIKE_UP, StationaryPieceType.SPIKE_DOWN, 
                    StationaryPieceType.SPIKE_LEFT, StationaryPieceType.SPIKE_RIGHT, 
                    StationaryPieceType.SPIKE_OMNI, StationaryPieceType.ROTATABLE_SPIKE}:
            color = (255, 0, 0) if stat != StationaryPieceType.ROTATABLE_SPIKE else (255, 165, 0) # Orange for rotatable
            pygame.draw.rect(screen, color, rect)
            center = rect.center
            
            # For ROTATABLE_SPIKE, we use global_direction to determine visual arrow
            effective_stat = stat
            if stat == StationaryPieceType.ROTATABLE_SPIKE and global_direction:
                spike_map = {
                    Direction.UP: StationaryPieceType.SPIKE_UP,
                    Direction.DOWN: StationaryPieceType.SPIKE_DOWN,
                    Direction.LEFT: StationaryPieceType.SPIKE_LEFT,
                    Direction.RIGHT: StationaryPieceType.SPIKE_RIGHT
                }
                effective_stat = spike_map[global_direction]

            if effective_stat == StationaryPieceType.SPIKE_OMNI:
                points = []
                for i in range(8):
                    angle = i * math.pi / 4
                    r = tile_size // 4 if i % 2 == 0 else tile_size // 8
                    points.append((center[0] + r * math.cos(angle), center[1] + r * math.sin(angle)))
                pygame.draw.polygon(screen, (255, 255, 255), points)
            elif effective_stat != StationaryPieceType.ROTATABLE_SPIKE:
                r = tile_size // 4
                arrow_map = {
                    StationaryPieceType.SPIKE_UP: (0, -r),
                    StationaryPieceType.SPIKE_DOWN: (0, r),
                    StationaryPieceType.SPIKE_LEFT: (-r, 0),
                    StationaryPieceType.SPIKE_RIGHT: (r, 0)
                }
                offset = arrow_map[effective_stat]
                tip = (center[0] + offset[0], center[1] + offset[1])
                if effective_stat == StationaryPieceType.SPIKE_UP:
                    pts = [tip, (tip[0]-10, tip[1]+15), (tip[0]+10, tip[1]+15)]
                elif effective_stat == StationaryPieceType.SPIKE_DOWN:
                    pts = [tip, (tip[0]-10, tip[1]-15), (tip[0]+10, tip[1]-15)]
                elif effective_stat == StationaryPieceType.SPIKE_LEFT:
                    pts = [tip, (tip[0]+15, tip[1]-10), (tip[0]+15, tip[1]+10)]
                else:
                    pts = [tip, (tip[0]-15, tip[1]-10), (tip[0]-15, tip[1]+10)]
                pygame.draw.polygon(screen, (255, 255, 255), pts)


class BoardSetup:
    def __init__(self, grid: np.ndarray, portals: List[Portal]):
        self.grid = grid
        self.portals = portals
        self.height, self.width = grid.shape
        self.portal_map = {p.loc: p for p in portals}

    def wrap_loc(self, loc: Loc) -> Loc:
        return Loc(loc.y % self.height, loc.x % self.width)

    def get_next_loc(self, loc: Loc, direction: Direction) -> Loc:
        """Finds the next non-VOID location in the given direction.
        If hitting a VOID, searches in the opposite direction for the other end of the non-VOID segment.
        """
        target = self.wrap_loc(loc + direction)
        if self.grid[target.y, target.x] != StationaryPieceType.VOID.value:
            return target
        
        # Hit a VOID. Per rules, move in opposite direction to find the "other side"
        # of the current non-VOID segment.
        opp_val = (-direction.value[0], -direction.value[1])
        opp_dir = next(d for d in Direction if d.value == opp_val)
        
        curr = loc
        while True:
            test = self.wrap_loc(curr + opp_dir)
            if self.grid[test.y, test.x] == StationaryPieceType.VOID.value:
                return curr
            curr = test
            if curr == loc:
                return loc

    def get_stationary_at(self, loc: Loc) -> StationaryPieceType:
        wrapped = self.wrap_loc(loc)
        return StationaryPieceType(self.grid[wrapped.y, wrapped.x])

    def get_portal_at(self, loc: Loc) -> Optional[Portal]:
        return self.portal_map.get(self.wrap_loc(loc))

    def get_other_portal(self, portal: Portal) -> Optional[Portal]:
        for p in self.portals:
            if p.portal_id == portal.portal_id and p != portal:
                return p
        return None

class SimState:
    """Internal helper to manage the simulation of a single move."""
    def __init__(self, setup: BoardSetup, droplets: List[Droplet], boxes: List[Box], boxes_with_spikes: List[BoxWithSpike], pearls: List[Pearl], gates: List[Gate], golden_walls: List[GoldenWall], hostile_droplets: List[HostileDroplet], global_direction: Optional[Direction] = None):
        self.setup = setup
        self.droplets = droplets
        self.boxes = boxes
        self.boxes_with_spikes = boxes_with_spikes
        self.pearls = pearls
        self.gates = gates
        self.golden_walls = golden_walls
        self.hostile_droplets = hostile_droplets
        self.global_direction = global_direction
        self.moving_pieces: Set[Movable] = set()
        self.to_remove: Set[Entity] = set()

class BoardState:
    def __init__(self, setup: BoardSetup, droplets: List[Droplet], boxes: List[Box], boxes_with_spikes: List[BoxWithSpike], pearls: List[Pearl], gates: List[Gate], golden_walls: List[GoldenWall], hostile_droplets: List[HostileDroplet], global_direction: Optional[Direction] = Direction.RIGHT):
        self.setup = setup
        self.droplets = sorted(droplets, key=lambda x: x.get_sort_key())
        self.boxes = sorted(boxes, key=lambda x: x.get_sort_key())
        self.boxes_with_spikes = sorted(boxes_with_spikes, key=lambda x: x.get_sort_key())
        self.pearls = sorted(pearls, key=lambda x: x.get_sort_key())
        self.gates = sorted(gates, key=lambda x: x.get_sort_key())
        self.golden_walls = sorted(golden_walls, key=lambda x: x.get_sort_key())
        self.hostile_droplets = sorted(hostile_droplets, key=lambda x: x.get_sort_key())
        self.global_direction = global_direction

    def get_id(self):
        return (
            tuple(d.get_sort_key() for d in self.droplets),
            tuple(b.get_sort_key() for b in self.boxes),
            tuple(b.get_sort_key() for b in self.boxes_with_spikes),
            tuple(p.get_sort_key() for p in self.pearls),
            tuple(g.get_sort_key() for g in self.gates),
            tuple(w.get_sort_key() for w in self.golden_walls),
            tuple(h.get_sort_key() for h in self.hostile_droplets),
            self.global_direction.name if self.global_direction else None
        )

    def is_solved(self):
        return len(self.pearls) == 0

    def get_droplet_count(self):
        return len(self.droplets)

    def get_next_state(self, droplet_idx: int, direction: Direction, include_intermediates: bool = False) -> Optional[Tuple['BoardState', List['BoardState']]]:
        # Fast manual cloning
        temp_droplets = [d.clone() for d in self.droplets]
        temp_boxes = [b.clone() for b in self.boxes]
        temp_boxes_with_spikes = [b.clone() for b in self.boxes_with_spikes]
        temp_pearls = [p.clone() for p in self.pearls]
        temp_gates = [g.clone() for g in self.gates]
        temp_golden_walls = [w.clone() for w in self.golden_walls]
        temp_hostile_droplets = [h.clone() for h in self.hostile_droplets]
        
        if include_intermediates:
            # Only assign UUIDs if they don't exist yet (for visualizer interpolation)
            for i, d in enumerate(temp_droplets): 
                if d._uuid is None: d._uuid = f"d{i}"
            for i, b in enumerate(temp_boxes):
                if b._uuid is None: b._uuid = f"b{i}"
            for i, b in enumerate(temp_boxes_with_spikes):
                if b._uuid is None: b._uuid = f"bs{i}"
            for i, p in enumerate(temp_pearls):
                if p._uuid is None: p._uuid = f"p{i}"
            for i, g in enumerate(temp_gates):
                if g._uuid is None: g._uuid = f"g{i}"
            for i, w in enumerate(temp_golden_walls):
                if w._uuid is None: w._uuid = f"w{i}"
            for i, h in enumerate(temp_hostile_droplets):
                if h._uuid is None: h._uuid = f"h{i}"

        sim = SimState(self.setup, temp_droplets, temp_boxes, temp_boxes_with_spikes, temp_pearls, temp_gates, temp_golden_walls, temp_hostile_droplets, global_direction=self.global_direction)
        sim.moving_pieces.add(sim.droplets[droplet_idx])
        
        # Build initial dynamic map for faster lookup
        sim.dynamic_map = {}
        for coll in [sim.droplets, sim.boxes, sim.boxes_with_spikes, sim.pearls, sim.gates, sim.golden_walls, sim.hostile_droplets]:
            for item in coll:
                sim.dynamic_map[item.loc.to_tuple()] = item

        # history tracks state signatures to detect infinite loops
        history = set()
        intermediate_states = []
        if include_intermediates:
            intermediate_states.append(BoardState(self.setup, [d.clone() for d in sim.droplets], 
                                                 [b.clone() for b in sim.boxes], 
                                                 [b.clone() for b in sim.boxes_with_spikes],
                                                 [p.clone() for p in sim.pearls], 
                                                 [g.clone() for g in sim.gates], 
                                                 [w.clone() for w in sim.golden_walls],
                                                 [h.clone() for h in sim.hostile_droplets],
                                                 global_direction=sim.global_direction))

        while sim.moving_pieces:
            # 1. Detect Infinite Loop
            # Only need a signature if we've moved. 
            # Note: We use a faster signature than full sort keys where possible.
            current_signature = (
                tuple((d.loc.to_tuple(), d.is_golden) for d in sim.droplets),
                tuple(b.loc.to_tuple() for b in sim.boxes),
                tuple((b.loc.to_tuple(), b.spike_dir.name) for b in sim.boxes_with_spikes),
                len(sim.pearls),
                tuple(g.is_closed for g in sim.gates),
                len(sim.golden_walls),
                len(sim.hostile_droplets),
                sim.global_direction
            )
            if current_signature in history:
                raise InfiniteLoopError("Infinite loop detected in move simulation")
            history.add(current_signature)

            # 2. Expand push chains
            changed = True
            while changed:
                changed = False
                for p in list(sim.moving_pieces):
                    target_loc = self.setup.get_next_loc(p.loc, direction)
                    target_ent = sim.dynamic_map.get(target_loc.to_tuple())
                    if isinstance(p, Droplet) and target_ent not in sim.moving_pieces:
                        if isinstance(target_ent, Box):
                            sim.moving_pieces.add(target_ent)
                            changed = True
                        elif isinstance(target_ent, BoxWithSpike):
                            # Push only if hitting non-spike side
                            if direction.value != (-target_ent.spike_dir.value[0], -target_ent.spike_dir.value[1]):
                                sim.moving_pieces.add(target_ent)
                                changed = True

            # 3. Identify who must stop
            to_stop = set()
            for p in list(sim.moving_pieces):
                target_loc = self.setup.get_next_loc(p.loc, direction)
                stat = self.setup.get_stationary_at(target_loc)
                
                # Stationary piece blockers
                if p.is_blocked_by_stationary(stat, direction, sim.global_direction):
                    to_stop.add(p)
                    continue
                
                # Droplet lethality check
                if isinstance(p, Droplet):
                    try:
                        p.handle_stationary_collision(stat, direction, sim.global_direction)
                    except ValueError:
                        sim.to_remove.add(p)
                        continue

                # Dynamic entity blockers (not in moving set)
                target_ent = sim.dynamic_map.get(target_loc.to_tuple())
                if target_ent and target_ent not in sim.moving_pieces:
                    # Special case: Golden Droplet hits Golden Wall
                    if isinstance(p, Droplet) and p.is_golden and isinstance(target_ent, GoldenWall):
                        # It can move into it (it will destroy it in execute step)
                        pass
                    elif not p.can_move_into(target_ent, direction):
                        to_stop.add(p)
                        continue
                
                # Gate blocking rule
                target_gate = None
                if isinstance(target_ent, Gate):
                    target_gate = target_ent
                
                if target_gate:
                    if target_gate.is_closed:
                        to_stop.add(p)
                    else:
                        # Open gate, check if someone else is currently AT the gate and LEAVING it
                        for other in sim.moving_pieces:
                            if other != p and other.loc == target_gate.loc:
                                to_stop.add(p)
                                break
                if p in to_stop: continue

            # Propagation of stop state (push chains)
            changed = True
            while changed:
                changed = False
                for p in list(sim.moving_pieces):
                    if p in to_stop: continue
                    target_loc = self.setup.get_next_loc(p.loc, direction)
                    target_ent = sim.dynamic_map.get(target_loc.to_tuple())
                    if target_ent in to_stop:
                        to_stop.add(p)
                        changed = True

            # Execute step for non-stopped pieces
            for p in to_stop:
                sim.moving_pieces.remove(p)
            
            if not sim.moving_pieces and not sim.to_remove: break

            # 4. Execute Step
            gates_to_toggle = []
            moving_list = list(sim.moving_pieces)
            
            # Remove moving pieces from map before updating their locations
            for p in moving_list:
                sim.dynamic_map.pop(p.loc.to_tuple(), None)

            for p in moving_list:
                if p in sim.to_remove: continue

                # Button logic
                if self.setup.get_stationary_at(p.loc) == StationaryPieceType.BUTTON:
                    sim.global_direction = direction

                # Leaving gate logic
                target_ent_at_curr = sim.dynamic_map.get(p.loc.to_tuple())
                if isinstance(target_ent_at_curr, Gate):
                    gates_to_toggle.append(target_ent_at_curr)
                else:
                    # If it's not in the map (e.g. multiple pieces at same loc), 
                    # we might need to find it in sim.gates
                    for g in sim.gates:
                        if g.loc == p.loc:
                            gates_to_toggle.append(g)
                            break

                p.loc = self.setup.get_next_loc(p.loc, direction)
                
                # Portal logic
                portal = self.setup.get_portal_at(p.loc)
                if portal:
                    other = self.setup.get_other_portal(portal)
                    if other: p.loc = other.loc
                
                # Interaction logic
                target_ent = sim.dynamic_map.get(p.loc.to_tuple())
                
                # Box with Spike logic
                if isinstance(p, Droplet) and isinstance(target_ent, BoxWithSpike):
                    sim.to_remove.add(p)
                elif isinstance(p, BoxWithSpike) and isinstance(target_ent, (Droplet, HostileDroplet)):
                    sim.to_remove.add(target_ent)
                # Golden logic: Golden Droplet hits Golden Wall
                elif isinstance(p, Droplet) and p.is_golden and isinstance(target_ent, GoldenWall):
                    sim.to_remove.add(target_ent)
                    p.is_golden = False
                elif isinstance(p, Droplet) and isinstance(target_ent, Pearl) and target_ent.is_golden:
                    p.is_golden = True
                    p.handle_collision(target_ent, sim)
                elif isinstance(p, Droplet) and isinstance(target_ent, Droplet):
                    # Merge logic: if one of them is golden, the merged droplet is golden.
                    p.is_golden = p.is_golden or target_ent.is_golden
                    p.handle_collision(target_ent, sim)
                else:
                    p.handle_collision(target_ent, sim)
                
                # Add/Update back to map if not removed
                if p not in sim.to_remove:
                    sim.dynamic_map[p.loc.to_tuple()] = p

            # Finalize step side effects
            for g in gates_to_toggle: g.is_closed = True
            for e in list(sim.to_remove):
                sim.dynamic_map.pop(e.loc.to_tuple(), None)
                if isinstance(e, Droplet):
                    if e in sim.droplets: sim.droplets.remove(e)
                elif isinstance(e, Box):
                    if e in sim.boxes: sim.boxes.remove(e)
                elif isinstance(e, BoxWithSpike):
                    if e in sim.boxes_with_spikes: sim.boxes_with_spikes.remove(e)
                elif isinstance(e, GoldenWall):
                    if e in sim.golden_walls: sim.golden_walls.remove(e)
                elif isinstance(e, HostileDroplet):
                    if e in sim.hostile_droplets: sim.hostile_droplets.remove(e)
                if e in sim.moving_pieces: sim.moving_pieces.remove(e)
            sim.to_remove.clear()
            # Re-sync map for safety
            sim.dynamic_map = {}
            for coll in [sim.droplets, sim.boxes, sim.boxes_with_spikes, sim.pearls, sim.gates, sim.golden_walls, sim.hostile_droplets]:
                for item in coll:
                    sim.dynamic_map[item.loc.to_tuple()] = item

            if include_intermediates:
                intermediate_states.append(BoardState(self.setup, [d.clone() for d in sim.droplets], 
                                                     [b.clone() for b in sim.boxes], 
                                                     [b.clone() for b in sim.boxes_with_spikes],
                                                     [p.clone() for p in sim.pearls], 
                                                     [g.clone() for g in sim.gates], 
                                                     [w.clone() for w in sim.golden_walls],
                                                     [h.clone() for h in sim.hostile_droplets],
                                                     global_direction=sim.global_direction))
            
            if not sim.pearls: # Immediate Win
                final_state = BoardState(self.setup, sim.droplets, sim.boxes, sim.boxes_with_spikes, sim.pearls, sim.gates, sim.golden_walls, sim.hostile_droplets, global_direction=sim.global_direction)
                return final_state, intermediate_states
            
            if not sim.droplets:
                return None

        final_state = BoardState(self.setup, sim.droplets, sim.boxes, sim.boxes_with_spikes, sim.pearls, sim.gates, sim.golden_walls, sim.hostile_droplets, global_direction=sim.global_direction)
        return final_state, intermediate_states


    def _get_dynamic_at(self, loc: Loc, sim: SimState, exclude: Optional[Entity] = None) -> Optional[Entity]:
        wrapped_loc = self.setup.wrap_loc(loc)
        for collection in [sim.droplets, sim.boxes, sim.boxes_with_spikes, sim.pearls, sim.gates, sim.golden_walls, sim.hostile_droplets]:
            for item in collection:
                if item == exclude: continue
                if item.loc == wrapped_loc: return item
        return None
