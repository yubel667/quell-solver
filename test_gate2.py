import unittest
import os
import board_io
from board import Direction

class TestGateMechanics2(unittest.TestCase):
    def test_toroidal_gate_close(self):
        # Load the test-gate2 level
        file_path = os.path.join(os.path.dirname(__file__), "questions/test-gate2.txt")
        with open(file_path, "r") as f:
            content = f.read()
        
        state = board_io.parse_board(content)
        
        # Initial state: Droplet at (1,1), Gate at (1,2), Pearl at (1,3)
        # Board width 6.
        # Move droplet LEFT.
        # It will wrap around, collect pearl at (1,3), pass through gate at (1,2), 
        # gate closes, then it hits the closed gate from the right.
        
        result = state.get_next_state(0, Direction.LEFT)
        self.assertIsNotNone(result, "Should find a result, not an infinite loop error or None")
        
        final_state, _ = result
        
        # Droplet should stop at (1,3) because gate at (1,2) is closed.
        self.assertEqual(final_state.droplets[0].loc.x, 3)
        self.assertEqual(final_state.droplets[0].loc.y, 1)
        self.assertTrue(final_state.gates[0].is_closed)
        # Pearl at (1,3) should be collected. 
        # Pearl at (2,3) remains.
        self.assertEqual(len(final_state.pearls), 1)

if __name__ == "__main__":
    unittest.main()
