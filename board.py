import numpy as np
from typing import List, Tuple, Dict, Optional, Set, Union
import enum
import copy

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

    def get_sort_key(self) -> Tuple:
        raise NotImplementedError()

    def render(self, screen, scale, camera_offset):
        pass

class Pearl(Entity):
    def get_sort_key(self):
        return ("p", self.loc.y, self.loc.x)

class Gate(Entity):
    def __init__(self, loc: Loc, is_closed: bool = False):
        super().__init__(loc)
        self.is_closed = is_closed

    def get_sort_key(self):
        return ("g", self.loc.y, self.loc.x, self.is_closed)

class Portal(Entity):
    def __init__(self, loc: Loc, portal_id: str):
        super().__init__(loc)
        self.portal_id = portal_id

    def get_sort_key(self):
        return ("o", self.portal_id, self.loc.y, self.loc.x)

class Movable(Entity):
    def can_move_into(self, target_entity: Optional[Entity], direction: Direction) -> bool:
        """Returns True if this piece can move into a cell occupied by target_entity."""
        raise NotImplementedError()

    def handle_collision(self, target_entity: Optional[Entity], state: 'SimState') -> bool:
        """Handles the effect of moving into target_entity. Returns True if piece should stop."""
        raise NotImplementedError()

    def is_blocked_by_stationary(self, stat: StationaryPieceType, direction: Direction) -> bool:
        raise NotImplementedError()

class Droplet(Movable):
    def get_sort_key(self):
        return ("d", self.loc.y, self.loc.x)

    def is_blocked_by_stationary(self, stat: StationaryPieceType, direction: Direction) -> bool:
        if stat == StationaryPieceType.WALL:
            return True
        # Spikes are handled in handle_stationary_collision for lethal check
        return False

    def handle_stationary_collision(self, stat: StationaryPieceType, direction: Direction):
        if stat in {StationaryPieceType.SPIKE_UP, StationaryPieceType.SPIKE_DOWN, 
                    StationaryPieceType.SPIKE_LEFT, StationaryPieceType.SPIKE_RIGHT, 
                    StationaryPieceType.SPIKE_OMNI}:
            if self._is_lethal(stat, direction):
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
        if isinstance(target, Box): return True # Can attempt to push
        if isinstance(target, Gate): return not target.is_closed
        if isinstance(target, Portal): return True
        return False

    def handle_collision(self, target: Optional[Entity], state: 'SimState'):
        if isinstance(target, Pearl):
            state.pearls.remove(target)
            return False
        if isinstance(target, Droplet):
            state.to_remove.add(target) # Merging
            return False
        if isinstance(target, Box):
            if target not in state.moving_pieces:
                state.moving_pieces.add(target)
            return False # Keep moving if box can move (checked in SimState.step)
        return False

class Box(Movable):
    def get_sort_key(self):
        return ("b", self.loc.y, self.loc.x)

    def is_blocked_by_stationary(self, stat: StationaryPieceType, direction: Direction) -> bool:
        if stat == StationaryPieceType.WALL: return True
        # Boxes treat all spikes as walls
        return stat in {StationaryPieceType.SPIKE_UP, StationaryPieceType.SPIKE_DOWN, 
                        StationaryPieceType.SPIKE_LEFT, StationaryPieceType.SPIKE_RIGHT, 
                        StationaryPieceType.SPIKE_OMNI}

    def can_move_into(self, target: Optional[Entity], direction: Direction) -> bool:
        if target is None: return True
        if isinstance(target, Gate): return not target.is_closed
        if isinstance(target, Portal): return True
        # Blocks against Droplets, Pearls, other Boxes (until annihilation)
        if isinstance(target, Box): return True 
        return False

    def handle_collision(self, target: Optional[Entity], state: 'SimState'):
        if isinstance(target, Box):
            state.to_remove.add(self)
            state.to_remove.add(target)
            return False
        return False

class BoardSetup:
    def __init__(self, grid: np.ndarray, portals: List[Portal]):
        self.grid = grid
        self.portals = portals
        self.height, self.width = grid.shape
        self.portal_map = {p.loc: p for p in portals}

    def get_stationary_at(self, loc: Loc) -> StationaryPieceType:
        if 0 <= loc.y < self.height and 0 <= loc.x < self.width:
            return StationaryPieceType(self.grid[loc.y, loc.x])
        return StationaryPieceType.WALL

    def get_portal_at(self, loc: Loc) -> Optional[Portal]:
        return self.portal_map.get(loc)

    def get_other_portal(self, portal: Portal) -> Optional[Portal]:
        for p in self.portals:
            if p.portal_id == portal.portal_id and p != portal:
                return p
        return None

class SimState:
    """Internal helper to manage the simulation of a single move."""
    def __init__(self, setup: BoardSetup, droplets: List[Droplet], boxes: List[Box], pearls: List[Pearl], gates: List[Gate]):
        self.setup = setup
        self.droplets = droplets
        self.boxes = boxes
        self.pearls = pearls
        self.gates = gates
        self.moving_pieces: Set[Movable] = set()
        self.to_remove: Set[Entity] = set()

class BoardState:
    def __init__(self, setup: BoardSetup, droplets: List[Droplet], boxes: List[Box], pearls: List[Pearl], gates: List[Gate]):
        self.setup = setup
        self.droplets = sorted(droplets, key=lambda x: x.get_sort_key())
        self.boxes = sorted(boxes, key=lambda x: x.get_sort_key())
        self.pearls = sorted(pearls, key=lambda x: x.get_sort_key())
        self.gates = sorted(gates, key=lambda x: x.get_sort_key())

    def get_id(self):
        return (
            tuple(d.get_sort_key() for d in self.droplets),
            tuple(b.get_sort_key() for b in self.boxes),
            tuple(p.get_sort_key() for p in self.pearls),
            tuple(g.get_sort_key() for g in self.gates)
        )

    def is_solved(self):
        return len(self.pearls) == 0

    def get_next_state(self, droplet_idx: int, direction: Direction) -> Optional['BoardState']:
        sim = SimState(self.setup, copy.deepcopy(self.droplets), copy.deepcopy(self.boxes), 
                       copy.deepcopy(self.pearls), copy.deepcopy(self.gates))
        sim.moving_pieces.add(sim.droplets[droplet_idx])
        
        # history tracks (piece_id, loc, direction) for all moving pieces to detect infinite loops
        history = set()

        while sim.moving_pieces:
            # 1. Detect Infinite Loop
            # We use a signature of all moving pieces. If the exact set of moving pieces 
            # with their locations and the global direction repeats, nothing new can happen.
            current_signature = tuple(sorted([(p.get_sort_key(), p.loc.to_tuple()) for p in sim.moving_pieces]))
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
                    if isinstance(target_ent, Box) and target_ent not in sim.moving_pieces:
                        sim.moving_pieces.add(target_ent)
                        changed = True

            # 3. Check for blockers
            can_move = True
            for p in sim.moving_pieces:
                target_loc = p.loc + direction
                stat = self.setup.get_stationary_at(target_loc)
                
                if p.is_blocked_by_stationary(stat, direction):
                    can_move = False; break
                
                if isinstance(p, Droplet):
                    try: p.handle_stationary_collision(stat, direction)
                    except ValueError: return None # Destroyed

                target_ent = self._get_dynamic_at(target_loc, sim)
                if target_ent and target_ent not in sim.moving_pieces:
                    if not p.can_move_into(target_ent, direction):
                        can_move = False; break

            if not can_move: break

            # 4. Execute Step
            gates_to_toggle = []
            for p in list(sim.moving_pieces):
                # Leaving gate
                old_ent = self._get_dynamic_at(p.loc, sim)
                if isinstance(old_ent, Gate): gates_to_toggle.append(old_ent)

                p.loc = p.loc + direction
                
                # Interaction logic
                p.handle_collision(self._get_dynamic_at(p.loc, sim), sim)

                # Portal logic
                portal = self.setup.get_portal_at(p.loc)
                if portal:
                    other = self.setup.get_other_portal(portal)
                    if other: p.loc = other.loc

            # Finalize step side effects
            for g in gates_to_toggle: g.is_closed = not g.is_closed
            for e in sim.to_remove:
                if isinstance(e, Droplet): sim.droplets.remove(e)
                elif isinstance(e, Box): sim.boxes.remove(e)
                if e in sim.moving_pieces: sim.moving_pieces.remove(e)
            sim.to_remove.clear()
            
            if not sim.pearls: # Immediate Win
                return BoardState(self.setup, sim.droplets, sim.boxes, sim.pearls, sim.gates)

        return BoardState(self.setup, sim.droplets, sim.boxes, sim.pearls, sim.gates)

    def _get_dynamic_at(self, loc: Loc, sim: SimState) -> Optional[Entity]:
        for collection in [sim.droplets, sim.boxes, sim.pearls, sim.gates]:
            for item in collection:
                if item.loc == loc: return item
        return None
