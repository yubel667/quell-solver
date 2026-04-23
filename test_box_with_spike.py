import unittest
import numpy as np
from board import BoardState, BoardSetup, Loc, Droplet, Box, BoxWithSpike, Direction, StationaryPieceType, HostileDroplet, Pearl

class TestBoxWithSpike(unittest.TestCase):
    def setUp(self):
        # 6x6 empty grid
        grid = np.zeros((6, 6), dtype=np.int8)
        self.setup = BoardSetup(grid, [])

    def test_push_non_spike_side(self):
        # 6x6 grid, put walls at x=5
        grid = np.zeros((6, 6), dtype=np.int8)
        grid[:, 5] = StationaryPieceType.WALL.value
        setup = BoardSetup(grid, [])

        # Droplet at (2,0) moves RIGHT. BoxWithSpike at (2,2) with spike pointing UP.
        # Droplet hits LEFT side (non-spike). BoxWithSpike should be pushed.
        droplet = Droplet(Loc(2, 0))
        box = BoxWithSpike(Loc(2, 2), Direction.UP)
        p = Pearl(Loc(0, 0))
        state = BoardState(setup, [droplet], [], [box], [p], [], [], [], global_direction=Direction.RIGHT)
        
        result = state.get_next_state(0, Direction.RIGHT)
        self.assertIsNotNone(result)
        final_state, _ = result
        
        # Droplet should be at (2,3), Box at (2,4)
        self.assertEqual(final_state.droplets[0].loc, Loc(2, 3))
        self.assertEqual(final_state.boxes_with_spikes[0].loc, Loc(2, 4))

    def test_hit_spike_side(self):
        # Droplet at (2,0) moves RIGHT. BoxWithSpike at (2,2) with spike pointing LEFT.
        # Droplet hits spike side. Droplet should be destroyed.
        droplet = Droplet(Loc(2, 0))
        box = BoxWithSpike(Loc(2, 2), Direction.LEFT)
        p = Pearl(Loc(0, 0))
        state = BoardState(self.setup, [droplet], [], [box], [p], [], [], [], global_direction=Direction.RIGHT)
        
        result = state.get_next_state(0, Direction.RIGHT)
        self.assertIsNone(result) # No droplets left

    def test_box_collision(self):
        # 6x6 grid, put walls at x=5
        grid = np.zeros((6, 6), dtype=np.int8)
        grid[:, 5] = StationaryPieceType.WALL.value
        setup = BoardSetup(grid, [])
        
        # Droplet at (2,0) moves RIGHT. BoxWithSpike at (2,1) (spike UP) pushes into normal Box at (2,3).
        # BoxWithSpike should stop at (2,2). Neither should disappear.
        droplet = Droplet(Loc(2, 0))
        bs = BoxWithSpike(Loc(2, 1), Direction.UP)
        b = Box(Loc(2, 3))
        state = BoardState(setup, [droplet], [b], [bs], [], [], [], [], global_direction=Direction.RIGHT)
        
        result = state.get_next_state(0, Direction.RIGHT)
        self.assertIsNotNone(result)
        final_state, _ = result
        
        self.assertEqual(len(final_state.boxes), 1)
        self.assertEqual(len(final_state.boxes_with_spikes), 1)
        self.assertEqual(final_state.boxes_with_spikes[0].loc, Loc(2, 2))
        self.assertEqual(final_state.boxes[0].loc, Loc(2, 3))

    def test_moving_spike_hits_droplets(self):
        # 6x6 grid, put wall at x=5
        grid = np.zeros((6, 6), dtype=np.int8)
        grid[:, 5] = StationaryPieceType.WALL.value
        setup = BoardSetup(grid, [])

        # Droplet1 at (2,0) pushes BoxWithSpike (spike RIGHT) at (2,1) into Droplet2 at (2,3) and HostileDroplet at (2,4).
        # Both Droplet2 and HostileDroplet should be destroyed, BoxWithSpike continues.
        d1 = Droplet(Loc(2, 0))
        bs = BoxWithSpike(Loc(2, 1), Direction.RIGHT)
        d2 = Droplet(Loc(2, 3))
        h = HostileDroplet(Loc(2, 4))
        # Need a pearl to not immediately win/end
        p = Pearl(Loc(0, 0))
        
        state = BoardState(setup, [d1, d2], [], [bs], [p], [], [], [h], global_direction=Direction.RIGHT)
        
        result = state.get_next_state(0, Direction.RIGHT)
        self.assertIsNotNone(result)
        final_state, _ = result
        
        # Only d1 should remain. d2 and h destroyed.
        self.assertEqual(len(final_state.droplets), 1)
        self.assertEqual(final_state.droplets[0].loc, Loc(2, 3)) # d1 moved to where d2 was
        self.assertEqual(len(final_state.hostile_droplets), 0)
        self.assertEqual(final_state.boxes_with_spikes[0].loc, Loc(2, 4)) # bs moved to where h was

if __name__ == "__main__":
    unittest.main()
