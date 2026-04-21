import unittest
import os
import board_io
from board import Direction

class TestGateMechanics(unittest.TestCase):
    def test_gate_closes_and_blocks(self):
        # Load the test-gate level
        file_path = os.path.join(os.path.dirname(__file__), "questions/test-gate.txt")
        with open(file_path, "r") as f:
            content = f.read()
        
        state = board_io.parse_board(content)
        
        # Initial state: Droplet at (1,1), Box at (1,3), Gate at (1,4), Pearl at (1,7)
        self.assertEqual(len(state.droplets), 1)
        self.assertEqual(len(state.boxes), 1)
        self.assertEqual(len(state.gates), 1)
        
        # Move droplet RIGHT
        result = state.get_next_state(0, Direction.RIGHT)
        self.assertIsNotNone(result)
        
        final_state, _ = result
        
        # Expected behavior:
        # Box passes gate and stops at (1,6) [before pearl at (1,7)]
        # Droplet is blocked by the closing gate and stops at (1,3) [before gate at (1,4)]
        
        self.assertEqual(final_state.droplets[0].loc.x, 3, "Droplet should stop before the gate")
        self.assertEqual(final_state.boxes[0].loc.x, 6, "Box should stop before the pearl")
        self.assertTrue(final_state.gates[0].is_closed, "Gate should be closed")

if __name__ == "__main__":
    unittest.main()
