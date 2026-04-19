import numpy as np
from typing import List
import enum


class Loc:
    def __init__(self, y, x):
        self.y = y
        self.x = x

class StationaryPieceType(enum.Enum):
    EMPTY = 0 # pure empty space
    WALL = 1
    FIX_SPIKE_UP = 2
    FIX_SPIKE_DOWN = 3
    FIX_SPIKE_LEFT = 4
    FIX_SPIKE_RIGHT = 5
    FIX_SPIKE_OMNI = 6

# anything immutable goes there.
class BoardSetup:
    def __init__(self, setup: np.array):
        # setup is a numpy array that also implicitly defines area size.
        assert setup.shape[0] > 0
        assert setup.shape[1] > 0
        self.setup = setup

# every piece has a 
class Piece:
    def __init__(self, loc: Loc):
        self.loc = loc

    def type() -> str:
        pass

    def get_sort_key():
        # for ordering the pieces.
        return (self.type(), self.loc.y, self.loc.x)

class Droplet(Piece):
    def __init__(self, loc: Loc):
        super().__init__(loc)

    def type() -> str:
        return "d"

# pearl is the main wincon of the game.
class Pearl(Piece):
    def __init__(self, loc: Loc):
        super().__init__(loc)

    def type():
        return "p"

class Direction(enum.Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class Move:
    # Anything that is movable.
    def __init__(self, piece: Piece, direction: Direction):
        self.droplet = droplet
        self.directions = direction

# For DFS purpose
class BoardState:

    def __init__(self, setup: BoardSetup, pieces: List[Piece]):
        self.setup = setup
        # key pieces sorted to generate board state key.
        self.pieces = sorted(pieces, key=lambda p: p.get_sort_key())
    
    # get a tuple tracking visted board states.
    def get_board_state_id():
        # concat all piece sort key should be enough, since sort key itself is a string.
        return tuple(p.get_sort_key() for p in self.pieces)
    
    def get_num_pearls(self):
        count = 0
        for piece in self.pieces:
            

    def get_all_potential_moves(self) -> List[Move]:
        moves = []
        for piece in self.pieces:
            if isinstance(piece, Droplet):
                for direction in Direction:
                    moves.append(Move(piece, direction))
        return moves

    # If cannot get next board state, return Failure.
    def get_next_board_state(self, move: Move) -> BoardState | None:
        # Sanity check
        for piece in self.pieces:
            if move.droplet == piece:
                break
        else:
            raise ValueError("Invalid move")
        # start simulation of the droplet
        movable_map = {}
        moving_pieces = [move]
