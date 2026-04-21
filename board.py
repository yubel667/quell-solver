import numpy as np
from typing import List, Tuple, Dict, Optional, Set, Union
import enum
import copy
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

    def get_sort_key(self) -> Tuple:
        raise NotImplementedError()

    def render(self, screen, px, py, tile_size):
        pass

class Pearl(Entity):
    def get_sort_key(self):
        return ("p", self.loc.y, self.loc.x)

    def render(self, screen, px, py, tile_size):
        center = (px + tile_size // 2, py + tile_size // 2)
        pygame.draw.circle(screen, (255, 255, 255), center, tile_size // 4)
        pygame.draw.circle(screen, (200, 200, 200), center, tile_size // 4, 1)

class Gate(Entity):
    def __init__(self, loc: Loc, is_closed: bool = False):
        super().__init__(loc)
        self.is_closed = is_closed

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
    def get_sort_key(self):
        return ("d", self.loc.y, self.loc.x)

    def render(self, screen, px, py, tile_size):
        center = (px + tile_size // 2, py + tile_size // 2)
        pygame.draw.circle(screen, (0, 255, 255), center, tile_size // 2 - 5)
        pygame.draw.circle(screen, (0, 200, 200), center, tile_size // 2 - 5, 2)

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
        if isinstance(target, (Pearl, Droplet)): return True
        if isinstance(target, Box): return True 
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

class StationaryPiece:
    @staticmethod
    def render(screen, stat: StationaryPieceType, px, py, tile_size, global_direction: Optional[Direction] = Direction.RIGHT):
        rect = pygame.Rect(px, py, tile_size, tile_size)
        if stat == StationaryPieceType.WALL:
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
    def __init__(self, setup: BoardSetup, droplets: List[Droplet], boxes: List[Box], pearls: List[Pearl], gates: List[Gate], global_direction: Optional[Direction] = None):
        self.setup = setup
        self.droplets = droplets
        self.boxes = boxes
        self.pearls = pearls
        self.gates = gates
        self.global_direction = global_direction
        self.moving_pieces: Set[Movable] = set()
        self.to_remove: Set[Entity] = set()

class BoardState:
    def __init__(self, setup: BoardSetup, droplets: List[Droplet], boxes: List[Box], pearls: List[Pearl], gates: List[Gate], global_direction: Optional[Direction] = Direction.RIGHT):
        self.setup = setup
        self.droplets = sorted(droplets, key=lambda x: x.get_sort_key())
        self.boxes = sorted(boxes, key=lambda x: x.get_sort_key())
        self.pearls = sorted(pearls, key=lambda x: x.get_sort_key())
        self.gates = sorted(gates, key=lambda x: x.get_sort_key())
        self.global_direction = global_direction

    def get_id(self):
        return (
            tuple(d.get_sort_key() for d in self.droplets),
            tuple(b.get_sort_key() for b in self.boxes),
            tuple(p.get_sort_key() for p in self.pearls),
            tuple(g.get_sort_key() for g in self.gates),
            self.global_direction.name if self.global_direction else None
        )

    def is_solved(self):
        return len(self.pearls) == 0

    def get_droplet_count(self):
        return len(self.droplets)

    def get_next_state(self, droplet_idx: int, direction: Direction) -> Optional[Tuple['BoardState', List['BoardState']]]:
        # Assign temporary UUIDs to all pieces to track them through sliding
        temp_droplets = copy.deepcopy(self.droplets)
        temp_boxes = copy.deepcopy(self.boxes)
        temp_pearls = copy.deepcopy(self.pearls)
        temp_gates = copy.deepcopy(self.gates)
        
        for i, d in enumerate(temp_droplets): d._uuid = f"d{i}"
        for i, b in enumerate(temp_boxes): b._uuid = f"b{i}"
        for i, p in enumerate(temp_pearls): p._uuid = f"p{i}"
        for i, g in enumerate(temp_gates): g._uuid = f"g{i}"

        sim = SimState(self.setup, temp_droplets, temp_boxes, temp_pearls, temp_gates, global_direction=self.global_direction)
        sim.moving_pieces.add(sim.droplets[droplet_idx])
        
        # history tracks (piece_id, loc, direction) for all moving pieces to detect infinite loops
        history = set()
        intermediate_states = [BoardState(self.setup, copy.deepcopy(sim.droplets), copy.deepcopy(sim.boxes), 
                                         copy.deepcopy(sim.pearls), copy.deepcopy(sim.gates), global_direction=sim.global_direction)]

        while sim.moving_pieces:
            # 1. Detect Infinite Loop
            # We must include the state of pearls and gates, as collecting a pearl 
            # or closing a gate changes the state and breaks what would otherwise be a loop.
            current_signature = (
                tuple(sorted(d.get_sort_key() for d in sim.droplets)),
                tuple(sorted(b.get_sort_key() for b in sim.boxes)),
                tuple(sorted(p.get_sort_key() for p in sim.pearls)),
                tuple(sorted(g.get_sort_key() for g in sim.gates)),
                sim.global_direction.name if sim.global_direction else None
            )
            if current_signature in history:
                raise InfiniteLoopError("Infinite loop detected in move simulation")
            history.add(current_signature)

            # 2. Expand push chains
            changed = True
            while changed:
                changed = False
                for p in list(sim.moving_pieces):
                    target_loc = p.loc + direction
                    target_ent = self._get_dynamic_at(target_loc, sim)
                    if isinstance(p, Droplet) and isinstance(target_ent, Box) and target_ent not in sim.moving_pieces:
                        sim.moving_pieces.add(target_ent)
                        changed = True

            # 3. Identify who must stop
            to_stop = set()
            for p in list(sim.moving_pieces):
                target_loc = p.loc + direction
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
                target_ent = self._get_dynamic_at(target_loc, sim)
                if target_ent and target_ent not in sim.moving_pieces:
                    if not p.can_move_into(target_ent, direction):
                        to_stop.add(p)
                        continue
                
                # Gate blocking rule: Block if gate is closed OR will be closed by someone else leaving it
                target_gate = None
                wrapped_target = self.setup.wrap_loc(target_loc)
                for g in sim.gates:
                    if g.loc == wrapped_target:
                        target_gate = g
                        break
                
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
                    target_loc = p.loc + direction
                    target_ent = self._get_dynamic_at(target_loc, sim)
                    # If target is someone who is stopping, we must also stop
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
            
            for p in moving_list:
                if p in sim.to_remove: continue

                # Button logic: Triggers upon LEAVING the current cell
                if self.setup.get_stationary_at(p.loc) == StationaryPieceType.BUTTON:
                    sim.global_direction = direction

                # Leaving gate: Find gate at current location before moving
                for g in sim.gates:
                    if g.loc == p.loc:
                        gates_to_toggle.append(g)
                        break

                p.loc = p.loc + direction
                
                # Portal logic
                portal = self.setup.get_portal_at(p.loc)
                if portal:
                    other = self.setup.get_other_portal(portal)
                    if other: p.loc = other.loc

                p.loc = self.setup.wrap_loc(p.loc)
                
                # Interaction logic
                target_ent = self._get_dynamic_at(p.loc, sim, exclude=p)
                p.handle_collision(target_ent, sim)

            # Finalize step side effects
            for g in gates_to_toggle: g.is_closed = True
            for e in list(sim.to_remove):
                if isinstance(e, Droplet):
                    if e in sim.droplets: sim.droplets.remove(e)
                elif isinstance(e, Box):
                    if e in sim.boxes: sim.boxes.remove(e)
                if e in sim.moving_pieces: sim.moving_pieces.remove(e)
            sim.to_remove.clear()
            
            # Save intermediate state for animation
            intermediate_states.append(BoardState(self.setup, copy.deepcopy(sim.droplets), copy.deepcopy(sim.boxes), 
                                                 copy.deepcopy(sim.pearls), copy.deepcopy(sim.gates), global_direction=sim.global_direction))
            
            if not sim.pearls: # Immediate Win
                final_state = BoardState(self.setup, sim.droplets, sim.boxes, sim.pearls, sim.gates, global_direction=sim.global_direction)
                return final_state, intermediate_states
            
            # If all droplets are gone but pearls remain, failure
            if not sim.droplets:
                return None

        final_state = BoardState(self.setup, sim.droplets, sim.boxes, sim.pearls, sim.gates, global_direction=sim.global_direction)
        return final_state, intermediate_states


    def _get_dynamic_at(self, loc: Loc, sim: SimState, exclude: Optional[Entity] = None) -> Optional[Entity]:
        wrapped_loc = self.setup.wrap_loc(loc)
        for collection in [sim.droplets, sim.boxes, sim.pearls, sim.gates]:
            for item in collection:
                if item == exclude: continue
                if item.loc == wrapped_loc: return item
        return None
