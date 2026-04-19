import unittest
import numpy as np
import board_io
from board import (
    BoardState, BoardSetup, Loc, Droplet, Box, Pearl, Portal, Gate, StationaryPieceType
)

class TestBoardIO(unittest.TestCase):
    def test_serialization_roundtrip(self):
        # Create a complex fake board with all entities
        grid = np.zeros((5, 5), dtype=np.int8)
        grid[0, 0] = StationaryPieceType.WALL.value
        grid[1, 1] = StationaryPieceType.SPIKE_UP.value
        grid[4, 4] = StationaryPieceType.SPIKE_OMNI.value
        
        portals = [
            Portal(Loc(0, 1), "A"),
            Portal(Loc(4, 3), "A")
        ]
        
        setup = BoardSetup(grid, portals)
        
        droplets = [Droplet(Loc(2, 2))]
        boxes = [Box(Loc(3, 3))]
        pearls = [Pearl(Loc(1, 2)), Pearl(Loc(2, 1))]
        gates = [Gate(Loc(4, 0), is_closed=True), Gate(Loc(0, 4), is_closed=False)]
        
        original_state = BoardState(setup, droplets, boxes, pearls, gates)
        
        # Serialize
        serialized = board_io.serialize_board(original_state)
        
        # Deserialize
        restored_state = board_io.parse_board(serialized)
        
        # Assert equality of ID (which covers all dynamic piece states and types)
        self.assertEqual(original_state.get_id(), restored_state.get_id())
        
        # Assert equality of setup
        np.testing.assert_array_equal(original_state.setup.grid, restored_state.setup.grid)
        self.assertEqual(len(original_state.setup.portals), len(restored_state.setup.portals))
        for p1, p2 in zip(original_state.setup.portals, restored_state.setup.portals):
            self.assertEqual(p1.loc, p2.loc)
            self.assertEqual(p1.portal_id, p2.portal_id)

if __name__ == "__main__":
    unittest.main()
